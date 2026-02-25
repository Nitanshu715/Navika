# finance_ai/login_page.py
import reflex as rx
from .auth_state import AuthState

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

html,body{margin:0;padding:0;background:#060a14;overflow:hidden;height:100%}

@keyframes fp{0%{transform:translateY(100vh) scale(0);opacity:0}6%{opacity:.5}94%{opacity:.1}100%{transform:translateY(-8vh) scale(1);opacity:0}}
.pt{position:fixed;border-radius:50%;pointer-events:none;z-index:0;animation:fp linear infinite}

@keyframes ob{0%,100%{transform:scale(1) translate(0,0);opacity:.4}50%{transform:scale(1.1) translate(18px,-22px);opacity:.62}}
.ob{position:fixed;border-radius:50%;filter:blur(78px);pointer-events:none;z-index:0}
.ob1{width:520px;height:520px;top:-190px;left:-170px;background:radial-gradient(circle,rgba(124,58,237,.21) 0%,transparent 70%);animation:ob 9s ease-in-out infinite}
.ob2{width:400px;height:400px;bottom:-140px;right:-110px;background:radial-gradient(circle,rgba(0,212,255,.15) 0%,transparent 70%);animation:ob 12s ease-in-out infinite 3s}
.ob3{width:270px;height:270px;top:44%;left:53%;background:radial-gradient(circle,rgba(16,185,129,.1) 0%,transparent 70%);animation:ob 7s ease-in-out infinite 6s}

.dg{position:fixed;inset:0;z-index:0;pointer-events:none;background-image:radial-gradient(rgba(0,212,255,.05) 1px,transparent 1px);background-size:42px 42px}

@keyframes sc{0%{top:-2px;opacity:0}6%{opacity:.8}94%{opacity:.4}100%{top:100vh;opacity:0}}
.sl{position:fixed;left:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,rgba(0,212,255,.55),transparent);z-index:1;pointer-events:none;animation:sc 7s linear infinite}

@keyframes gf{0%,100%{transform:translateY(0);opacity:.11}50%{transform:translateY(-11px);opacity:.27}}
.gp{position:fixed;pointer-events:none;z-index:1;font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(0,212,255,.28);animation:gf ease-in-out infinite}

/* WRAPPER: position:fixed so the page never scrolls — card always centers */
.aw{position:fixed;inset:0;z-index:10;display:flex;align-items:center;justify-content:center;padding:12px;overflow-y:auto}

@keyframes ci{from{opacity:0;transform:translateY(32px) scale(.95);filter:blur(5px)}to{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}}
.ac{width:100%;max-width:416px;background:rgba(11,17,32,.94);backdrop-filter:blur(22px) saturate(1.4);border:1px solid rgba(26,47,80,.9);border-radius:20px;padding:26px 34px 22px;box-shadow:0 0 0 1px rgba(0,212,255,.05),0 32px 80px rgba(0,0,0,.68),inset 0 1px 0 rgba(255,255,255,.05);animation:ci .7s cubic-bezier(.34,1.4,.64,1) both;position:relative;flex-shrink:0}

@keyframes cp{0%,100%{opacity:.22}50%{opacity:.85}}
.ctl,.cbr{position:absolute;width:17px;height:17px;pointer-events:none;animation:cp 3s ease-in-out infinite}
.ctl{top:-1px;left:-1px;border-top:2px solid #00d4ff;border-left:2px solid #00d4ff;border-radius:5px 0 0 0}
.cbr{bottom:-1px;right:-1px;border-bottom:2px solid #7c3aed;border-right:2px solid #7c3aed;border-radius:0 0 5px 0;animation-delay:1.5s}

@keyframes lg{0%,100%{filter:drop-shadow(0 0 7px #00d4ff)}50%{filter:drop-shadow(0 0 18px #00d4ff)}}
.li{animation:lg 3.5s ease-in-out infinite;display:inline-block}

@keyframes rv{from{opacity:0;transform:translateY(13px)}to{opacity:1;transform:translateY(0)}}
.r0{animation:rv .38s ease .04s both}.r1{animation:rv .38s ease .11s both}.r2{animation:rv .38s ease .18s both}
.r3{animation:rv .38s ease .25s both}.r4{animation:rv .38s ease .32s both}.r5{animation:rv .38s ease .39s both}
.r6{animation:rv .38s ease .46s both}

.gb{width:100%;padding:9px 13px;cursor:pointer;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);border-radius:10px;display:flex;align-items:center;justify-content:center;gap:8px;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:#e2e8f0;transition:all .2s ease}
.gb:hover{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.18);transform:translateY(-1px)}

.dv{display:flex;align-items:center;gap:9px;margin:12px 0 13px}
.dl{flex:1;height:1px;background:linear-gradient(90deg,transparent,#1a2f50,transparent)}
.dt{font-size:10px;color:#4a6080;letter-spacing:.12em;font-family:'JetBrains Mono',monospace;white-space:nowrap}

.iw{margin-bottom:10px}
.il{display:block;font-size:10px;font-weight:700;color:#4a6080;letter-spacing:.14em;margin-bottom:5px;font-family:'JetBrains Mono',monospace}
.ir{position:relative}
.if{width:100%;padding:9px 36px 9px 12px;background:rgba(6,10,20,.96);border:1px solid #1a2f50;border-radius:8px;font-family:'JetBrains Mono',monospace;font-size:13px;color:#e2e8f0;outline:none;transition:all .2s ease;box-sizing:border-box;display:block}
.if:focus{border-color:#00d4ff;box-shadow:0 0 0 3px rgba(0,212,255,.08)}
.if::placeholder{color:#4a6080}
.ic{position:absolute;right:10px;top:50%;transform:translateY(-50%);color:#4a6080;font-size:12px;user-select:none;pointer-events:none}
.ic.cl{cursor:pointer;pointer-events:all;transition:color .15s}
.ic.cl:hover{color:#00d4ff}

.pbl{font-size:10px;color:#4a6080;margin-top:3px;font-family:'JetBrains Mono',monospace;min-height:13px}

.sb{width:100%;padding:11px;margin-top:4px;background:linear-gradient(135deg,#7c3aed,#5b21b6);border:none;border-radius:9px;font-family:'Syne',sans-serif;font-size:13px;font-weight:900;color:white;cursor:pointer;letter-spacing:.07em;position:relative;overflow:hidden;transition:all .2s ease;box-shadow:0 4px 16px rgba(124,58,237,.4),inset 0 1px 0 rgba(255,255,255,.1)}
.sb::before{content:'';position:absolute;top:-50%;left:-70%;width:48%;height:200%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.17),transparent);transform:skewX(-18deg);transition:left .5s ease}
.sb:hover::before{left:130%}
.sb:hover{transform:translateY(-1px);box-shadow:0 7px 25px rgba(124,58,237,.52)}
.sb:disabled{opacity:.55;cursor:not-allowed;transform:none}

@keyframes mi{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
.ok{padding:9px 12px;border-radius:8px;margin-top:8px;background:rgba(16,185,129,.09);border:1px solid rgba(16,185,129,.24);color:#10b981;font-size:12px;font-weight:700;text-align:center;animation:mi .3s ease both}
.er{padding:9px 12px;border-radius:8px;margin-top:8px;background:rgba(239,68,68,.09);border:1px solid rgba(239,68,68,.24);color:#ef4444;font-size:12px;font-weight:700;text-align:center;animation:mi .3s ease both}

.tos{display:flex;align-items:flex-start;gap:7px;margin:8px 0}
.tos input{accent-color:#7c3aed;margin-top:3px;flex-shrink:0}
.tos label{font-size:11px;color:#4a6080;line-height:1.55}
.tos a{color:#00d4ff;text-decoration:none}

.ft{text-align:center;margin-top:13px;font-size:10px;color:#4a6080;font-family:'JetBrains Mono',monospace;letter-spacing:.05em}
.fg{font-size:11px;color:#4a6080;background:none;border:none;cursor:pointer;font-family:'JetBrains Mono',monospace;transition:color .15s;padding:0}
.fg:hover{color:#00d4ff}
</style>"""

PJS = """<script>
(function(){
  var c=['#00d4ff','#7c3aed','#10b981','#f59e0b'];
  for(var i=0;i<30;i++){
    var d=document.createElement('div'),cl=c[i%4],s=Math.random()*2+.4;
    d.className='pt';
    d.style.cssText='width:'+s+'px;height:'+s+'px;left:'+(Math.random()*100)+
      '%;background:'+cl+';filter:drop-shadow(0 0 3px '+cl+');'+
      'animation-duration:'+(Math.random()*10+8)+'s;animation-delay:'+(Math.random()*9)+'s';
    document.body.appendChild(d);
  }
})();
</script>"""

GOOGLE_SVG = """<svg width="17" height="17" viewBox="0 0 48 48">
<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
</svg>"""


def _bg():
    glyphs = [("FAISS.k=5","9%","5%","11s","0s"),("risk:Med","72%","3%","13s","2s"),
              ("dim:384","17%","91%","10s","5s"),("₹14,283","79%","88%","9s","1s"),("σ=2.3","43%","93%","13s","8s")]
    return rx.fragment(
        rx.html(CSS), rx.html(PJS),
        rx.box(class_name="ob ob1"), rx.box(class_name="ob ob2"), rx.box(class_name="ob ob3"),
        rx.box(class_name="dg"), rx.box(class_name="sl"),
        *[rx.box(rx.text(t, font_size="10px"), class_name="gp",
                 style={"top":top,"left":left,"animation-duration":d,"animation-delay":dl})
          for t,top,left,d,dl in glyphs],
    )


def _logo():
    return rx.vstack(
        rx.text("◈", font_size="30px", color="#00d4ff", class_name="li r0"),
        rx.text("FINSIGHT", font_size="16px", font_weight="900", color="#e2e8f0",
                letter_spacing="0.22em", font_family="'JetBrains Mono',monospace", class_name="r0"),
        rx.text("AI FINANCIAL INTELLIGENCE", font_size="9px", color="#4a6080",
                letter_spacing="0.15em", class_name="r0"),
        spacing="1", align="center", style={"text-align":"center","margin-bottom":"2px"},
    )


def _tabs():
    def tab_style(name):
        active = AuthState.active_tab == name
        return {
            "flex":"1","padding":"8px 4px","border":"none","border-radius":"7px",
            "cursor":"pointer","font-family":"'Syne',sans-serif","font-size":"12px",
            "font-weight":"800","letter-spacing":"0.03em","transition":"all 0.22s ease",
            "background": rx.cond(active, "linear-gradient(135deg,#7c3aed,#5b21b6)", "transparent"),
            "color":       rx.cond(active, "white", "#4a6080"),
            "box-shadow":  rx.cond(active, "0 3px 12px rgba(124,58,237,.4)", "none"),
        }
    return rx.hstack(
        rx.button("Sign In",        on_click=AuthState.switch_tab("login"),  style=tab_style("login")),
        rx.button("Create Account", on_click=AuthState.switch_tab("signup"), style=tab_style("signup")),
        class_name="r1",
        style={"display":"flex","gap":"3px","width":"100%",
               "background":"rgba(6,10,20,.95)","border":"1px solid rgba(26,47,80,.85)",
               "border-radius":"9px","padding":"3px","margin":"13px 0 15px"},
        width="100%",
    )


def _google_btn():
    return rx.box(
        rx.hstack(rx.html(GOOGLE_SVG),
                  rx.text("Continue with Google", font_size="13px", font_weight="700",
                          color="#e2e8f0", font_family="'Syne',sans-serif"),
                  spacing="2", align="center", justify="center", width="100%"),
        class_name="gb r2", on_click=AuthState.google_login, cursor="pointer",
    )


def _divider():
    return rx.html('<div class="dv r3"><div class="dl"></div>'
                   '<span class="dt">OR USE EMAIL</span><div class="dl"></div></div>')


def _inp(label, placeholder, on_change, value,
         itype="text", icon="", reveal=False, anim="r4"):
    eye = rx.cond(
        reveal,
        rx.text(rx.cond(AuthState.show_pw, "(0)", "👁"), class_name="ic cl",
                on_click=AuthState.toggle_pw,
                style={"position":"absolute","right":"10px","top":"50%",
                       "transform":"translateY(-50%)","cursor":"pointer",
                       "user-select":"none","pointer-events":"all"}),
        rx.text(icon, class_name="ic",
                style={"position":"absolute","right":"10px","top":"50%",
                       "transform":"translateY(-50%)","pointer-events":"none"})
        if icon else rx.box(),
    )
    return rx.box(
        rx.html(f'<label class="il">{label}</label>'),
        rx.box(
            rx.input(
                placeholder=placeholder, on_change=on_change, value=value,
                type=rx.cond(AuthState.show_pw & reveal, "text", itype) if reveal else itype,
                class_name="if", width="100%", color="#e2e8f0",
                font_family="'JetBrains Mono',monospace", font_size="13px",
                style={"border":"1px solid #1a2f50","background":"rgba(6,10,20,.96)",
                       "outline":"none","padding":"9px 36px 9px 12px"},
                _placeholder={"color":"#4a6080"},
                _focus={"border":"1px solid #00d4ff","box-shadow":"0 0 0 3px rgba(0,212,255,.08)"},
            ),
            eye,
            class_name="ir", position="relative",
        ),
        class_name=f"iw {anim}",
    )


def _pw_strength():
    def bar(n):
        bg = rx.cond(AuthState.pw_strength >= n,
                     rx.cond(AuthState.pw_strength == 1, "#ef4444",
                             rx.cond(AuthState.pw_strength == 2, "#f59e0b", "#10b981")),
                     "#1a2f50")
        return rx.box(style={"flex":"1","height":"3px","border-radius":"2px",
                              "transition":"all .3s ease","background":bg})
    return rx.vstack(
        rx.hstack(bar(1), bar(2), bar(3),
                  style={"display":"flex","gap":"3px","margin-top":"5px","width":"100%"}),
        rx.text(rx.cond(AuthState.pw_strength == 0, " ",
                        rx.cond(AuthState.pw_strength == 1, "Weak",
                                rx.cond(AuthState.pw_strength == 2, "Medium", "Strong ✓"))),
                class_name="pbl"),
        spacing="0", width="100%",
    )


def _submit(label, handler):
    return rx.button(
        rx.cond(AuthState.is_loading,
                rx.hstack(rx.spinner(color="white", size="2"),
                          rx.text("Processing…", font_size="13px", font_weight="900"),
                          spacing="2", align="center"),
                rx.text(label, font_size="13px", font_weight="900", letter_spacing=".07em")),
        on_click=handler, disabled=AuthState.is_loading,
        class_name="sb r6", width="100%",
        background="transparent", border="none", color="white",
        cursor="pointer", type="button",
    )


def _status():
    return rx.vstack(
        rx.cond(AuthState.error_msg != "",
                rx.box(rx.text(AuthState.error_msg, font_size="12px",
                               font_weight="700", color="#ef4444"), class_name="er"),
                rx.box()),
        rx.cond(AuthState.success_msg != "",
                rx.box(rx.text(AuthState.success_msg, font_size="12px",
                               font_weight="700", color="#10b981"), class_name="ok"),
                rx.box()),
        spacing="0", width="100%",
    )


def _login_form():
    return rx.vstack(
        _inp("EMAIL", "you@example.com",
             AuthState.set_login_email, AuthState.login_email, "email", "✉", anim="r3"),
        _inp("PASSWORD", "Your password",
             AuthState.set_login_password, AuthState.login_password,
             "password", "", reveal=True, anim="r4"),
        rx.hstack(
            rx.spacer(),
            rx.button("Forgot password?", on_click=AuthState.forgot_password,
                      class_name="fg", type="button", background="none", border="none",
                      cursor="pointer", color="#4a6080", font_size="11px",
                      font_family="'JetBrains Mono',monospace", _hover={"color":"#00d4ff"}),
            width="100%", margin_bottom="2px",
        ),
        _submit("◈  SIGN IN TO FINSIGHT", AuthState.login),
        _status(),
        spacing="0", width="100%",
    )


def _signup_form():
    return rx.vstack(
        _inp("FULL NAME", "Your name",
             AuthState.set_signup_name, AuthState.signup_name, "text", "◎", anim="r3"),
        _inp("EMAIL", "you@example.com",
             AuthState.set_signup_email, AuthState.signup_email, "email", "✉", anim="r4"),
        _inp("PASSWORD", "Min 8 chars",
             AuthState.set_signup_password, AuthState.signup_password,
             "password", "", reveal=True, anim="r5"),
        _pw_strength(),
        rx.html("""<div class="tos r5"><input type="checkbox" id="tc">
          <label for="tc">I agree to the <a href="#">Terms</a> and <a href="#">Privacy Policy</a></label>
        </div>"""),
        _submit("⊕  CREATE MY ACCOUNT", AuthState.sign_up),
        _status(),
        spacing="0", width="100%",
    )


def login_page() -> rx.Component:
    return rx.box(
        _bg(),
        rx.box(
            rx.box(
                rx.html('<div class="ctl"></div><div class="cbr"></div>'),
                _logo(),
                _tabs(),
                _google_btn(),
                _divider(),
                rx.cond(AuthState.active_tab == "login", _login_form(), _signup_form()),
                rx.box(rx.text("✓  30-day sessions · AES-256 encrypted",
                               font_size="10px", color="#4a6080",
                               font_family="'JetBrains Mono',monospace", letter_spacing=".05em"),
                       class_name="ft r6"),
                class_name="ac",
            ),
            class_name="aw",
        ),
        style={"position":"fixed","inset":"0","background":"#060a14","overflow":"hidden"},
        on_mount=AuthState.check_and_redirect,
    )


def verified_page() -> rx.Component:
    return rx.box(
        _bg(),
        rx.box(
            rx.box(
                rx.html('<div class="ctl"></div><div class="cbr"></div>'),
                rx.vstack(
                    rx.text("◈", font_size="36px", color="#00d4ff", class_name="li r0"),
                    rx.text("✓", font_size="50px", color="#10b981", class_name="r1",
                            style={"line-height":"1"}),
                    rx.text("Email Verified!", font_size="22px", font_weight="900",
                            color="#e2e8f0", font_family="'Syne',sans-serif", class_name="r2"),
                    rx.text("Your account is now active.", font_size="13px", color="#4a6080",
                            font_family="'JetBrains Mono',monospace", class_name="r3"),
                    rx.button("→  OPEN DASHBOARD", on_click=rx.redirect("/"),
                              class_name="sb r4", background="transparent", border="none",
                              color="white", cursor="pointer",
                              style={"margin-top":"8px","padding":"11px 24px"}),
                    spacing="3", align="center",
                    style={"text-align":"center","padding":"5px 0"},
                ),
                class_name="ac",
            ),
            class_name="aw",
        ),
        style={"position":"fixed","inset":"0","background":"#060a14","overflow":"hidden"},
    )