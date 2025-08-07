# banking_funnel_apples_v4.py  – v4: depositors’ interest highlighted

import pygame as pg, random, sys

# ───────────────────────── CONFIG ──────────────────────────────
WIDTH, HEIGHT        = 700, 1000
FPS                  = 60
YEARS_PER_SECOND     = 4
INTEREST_PCT         = 6        # annual % (compound) on deposits
CREDIT_MULT          = 3        # credit grows 3× faster → 18%/yr
NUM_AGENTS           = 500
TOP_PERCENTILE       = 0.01
RESET_AT_SHARE       = 0.50     # restart when elite own ≥ 50 %
START_BALANCE        = 100.0

# COLORS
PRINCIPAL_CLR = (230,  60,  60)    # red
CREDIT_CLR    = (255, 180,   0)    # orange
INTEREST_CLR  = (100, 255, 100)    # green  for depositors' interest
STEM_CLR      = ( 60, 160,  60)
BG_TOP        = (  15,  15,  35)
BG_BOT        = (  35,  35,  75)
FUNNEL_CLR    = (100, 200, 255)
HUD_CLR       = (250, 250, 250)

# layout + styling
FUN_L, FUN_R, FUN_TOP = 130, 130, 110
THROAT_W             = 160
APPLE_RADIUS         = 12
STEM_WIDTH           = 3
HUD_FNT_SIZE         = 28
LEG_FNT_SIZE         = 20

# derived rates
FRAMES_PER_YEAR = FPS * YEARS_PER_SECOND
r_pf = (1 + INTEREST_PCT/100)**(1/FRAMES_PER_YEAR) - 1
r_cf = (1 + (INTEREST_PCT * CREDIT_MULT)/100)**(1/FRAMES_PER_YEAR) - 1

# ─────────────────────── INIT ──────────────────────────────────
pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
clock  = pg.time.Clock()
hud_f = pg.font.SysFont("Arial", HUD_FNT_SIZE, bold=True)
leg_f = pg.font.SysFont("Arial", LEG_FNT_SIZE, bold=True)

def bounds(y):
    t = (y - FUN_TOP) / (HEIGHT - 50 - FUN_TOP)
    left  = FUN_L*(1-t) + (WIDTH/2-THROAT_W/2)*t
    right = WIDTH-FUN_R*(1-t) - (WIDTH/2-THROAT_W/2)*t
    return left, right

class Apple:
    def __init__(self, kind="principal"):
        self.kind = kind
        self.reset(first=True)

    def reset(self, first=False):
        self.wealth = START_BALANCE
        if first and self.kind=="principal":
            self.y = random.uniform(FUN_TOP+30, HEIGHT-50)
        else:
            self.y = HEIGHT-50 + random.uniform(-20,20)
        lx, rx = bounds(self.y)
        self.x = random.uniform(lx+APPLE_RADIUS, rx-APPLE_RADIUS)

    def update(self):
        global credit_buffer
        rate = r_pf if self.kind=="principal" else r_cf
        old_w = self.wealth
        self.wealth *= (1 + rate)
        if self.kind=="principal":
            credit_buffer += (self.wealth - old_w)
        target_y = HEIGHT-50 - (self.wealth/(START_BALANCE*25))*(HEIGHT-180)
        self.y += (target_y - self.y)*0.08
        l, r = bounds(self.y)
        self.x = min(max(self.x, l+APPLE_RADIUS), r-APPLE_RADIUS)

    def draw(self):
        clr = PRINCIPAL_CLR if self.kind=="principal" else CREDIT_CLR
        pg.draw.circle(screen, clr, (int(self.x), int(self.y)), APPLE_RADIUS)
        pg.draw.rect(screen, STEM_CLR,
                     (int(self.x)-STEM_WIDTH//2, int(self.y)-APPLE_RADIUS-8,
                      STEM_WIDTH, 8))
        pg.draw.line(screen, (255,255,255,40),
                     (int(self.x),int(self.y)+APPLE_RADIUS),
                     (int(self.x),int(self.y)+APPLE_RADIUS+10), 1)

def restart(apples):
    for a in apples:
        a.reset(first=False)

# initial apples
apples = [Apple("principal") for _ in range(NUM_AGENTS)]
initial_total     = NUM_AGENTS * START_BALANCE
frame             = 0
credit_buffer     = 0.0

# ─────────────────────── MAIN LOOP ─────────────────────────────
while True:
    for ev in pg.event.get():
        if ev.type in (pg.QUIT, pg.KEYDOWN) and getattr(ev, "key",None)==pg.K_ESCAPE:
            pg.quit(); sys.exit()

    # update apples & buffer
    for a in apples:
        a.update()

    # spawn credit apples
    while credit_buffer >= START_BALANCE:
        apples.append(Apple("credit"))
        credit_buffer -= START_BALANCE

    # recalc totals
    principal_total       = sum(a.wealth for a in apples if a.kind=="principal")
    credit_total          = sum(a.wealth for a in apples if a.kind=="credit")
    depositors_interest   = principal_total - initial_total
    tot                   = principal_total + credit_total
    extra                 = tot - initial_total

    # elite share
    elite_cut   = max(1, int(NUM_AGENTS * TOP_PERCENTILE))
    top_wealths = sorted((a.wealth for a in apples), reverse=True)
    elite_share = sum(top_wealths[:elite_cut]) / tot * 8

    if elite_share >= RESET_AT_SHARE:
        restart(apples)
        apples           = apples[:NUM_AGENTS]
        frame            = 0
        credit_buffer    = 0.0
        continue

    # draw gradient background
    for y in range(HEIGHT):
        r = y/HEIGHT
        col = (
            int(BG_TOP[0]*(1-r) + BG_BOT[0]*r),
            int(BG_TOP[1]*(1-r) + BG_BOT[1]*r),
            int(BG_TOP[2]*(1-r) + BG_BOT[2]*r),
        )
        pg.draw.line(screen, col, (0,y),(WIDTH,y))

    # funnel walls
    pg.draw.line(screen, FUNNEL_CLR, (FUN_L,HEIGHT-50), (WIDTH/2-THROAT_W/2,FUN_TOP), 5)
    pg.draw.line(screen, FUNNEL_CLR, (WIDTH-FUN_R,HEIGHT-50),(WIDTH/2+THROAT_W/2,FUN_TOP), 5)
    pg.draw.rect(screen, FUNNEL_CLR, (WIDTH/2-THROAT_W/2, FUN_TOP-8, THROAT_W, 8))

    # draw apples
    for a in apples:
        a.draw()

    # HUD (left)
    hud_x, hud_y = 20, 20
    lines = [
        f"Years:   {frame/FRAMES_PER_YEAR:4.1f}",
        f"Deposits:{principal_total:>10,.0f} ₳",
        f"Credit:  {credit_total:>10,.0f} ₳",
        f"Total:   {tot:>10,.0f} ₳",
        f"Elite 1%:{elite_share*100:>9.1f}%",
    ]
    for i, txt in enumerate(lines):
        screen.blit(hud_f.render(txt, True, HUD_CLR),
                    (hud_x, hud_y + i*(HUD_FNT_SIZE+4)))

    # HUD (right) – depositors' interest
    int_txt = f"Interest Earned: {depositors_interest:,.0f} ₳"
    screen.blit(hud_f.render(int_txt, True, INTEREST_CLR),
                (WIDTH-360, 20))

    # legend (bottom right)
    lx, ly = WIDTH-320, 100
    pg.draw.circle(screen, PRINCIPAL_CLR, (lx, ly), APPLE_RADIUS)
    screen.blit(leg_f.render("Depositor Principal", True, HUD_CLR), (lx+25, ly-12))
    pg.draw.circle(screen, CREDIT_CLR, (lx, ly+40), APPLE_RADIUS)
    screen.blit(leg_f.render("Bank Credit/Debt", True, HUD_CLR), (lx+25, ly+28))
    pg.draw.rect(screen, INTEREST_CLR, (lx-APPLE_RADIUS, ly+80, APPLE_RADIUS*2, APPLE_RADIUS*2))
    screen.blit(leg_f.render("Interest Earned", True, HUD_CLR), (lx+25, ly+75))

    # labels
    screen.blit(hud_f.render("← New Credit In", True, HUD_CLR),
                (WIDTH/2 - 140, HEIGHT-30))
    screen.blit(hud_f.render("Top 1% →", True, HUD_CLR),
                (WIDTH/2+THROAT_W//2+10, FUN_TOP-35))

    pg.display.flip()
    clock.tick(FPS)
    frame += 1
