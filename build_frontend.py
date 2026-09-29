"""Build frontend/index.html from docs/index.html: fetch data from the API
instead of embedding it, and add accounts / saved matchups / watchlist."""
import re

SRC = "/home/hatch/workspace/waiverwire/docs/index.html"
DST = "/home/hatch/workspace/waiverwire/frontend/index.html"

lines = open(SRC).read().split("\n")

# --- 1. Drop the embedded data; it now comes from /api/board and /api/pool. ---
assert lines[471].strip().startswith("const DATA = "), lines[471][:40]
assert lines[472].strip().startswith("const POOL = "), lines[472][:40]
assert lines[473].strip() == "const players = DATA.players;", lines[473][:60]
lines[471] = "    let DATA = null;"
lines[472] = "    let POOL = [];"
lines[473] = "    let players = [];"
print("data lines replaced, dropped", len(lines[471]) + len(lines[472]), "chars of literal")

src = "\n".join(lines)

# --- 2. featured and poolNorm are computed from data; defer them to boot. ---
old = "    const featured = players.find(p => p.priority) || players[0];"
assert old in src
src = src.replace(old, "    let featured = null;")

old = "    const poolNorm = POOL.map(p => normName(p.name));"
assert old in src
src = src.replace(old, "    let poolNorm = [];")

# --- 3. Boot: fetch data first, then render. ---
old = """    renderFeatured();
    renderQueue();
    renderBoard();

    /* ---------- matchup ---------- */"""
assert old in src
src = src.replace(
    old,
    """    async function boot() {
      try {
        const [board, pool] = await Promise.all([
          fetch('/api/board').then(r => { if (!r.ok) throw new Error('board'); return r.json(); }),
          fetch('/api/pool').then(r => { if (!r.ok) throw new Error('pool'); return r.json(); })
        ]);
        DATA = board;
        POOL = pool.players;
        players = DATA.players;
        featured = players.find(p => p.priority) || players[0];
        poolNorm = POOL.map(p => normName(p.name));
      } catch (err) {
        document.getElementById('board').innerHTML =
          '<p class="mu-note">Could not load player data. Check your connection and reload.</p>';
        throw err;
      }
      const lastWeek = DATA.week;
      document.querySelector('.season').innerHTML =
        '<span><i class="live-dot"></i>' + DATA.season + ' season</span>' +
        '<span>Through Week ' + lastWeek + '</span><span>PPR scoring</span>';
      document.querySelector('header.top h1').innerHTML = 'Week ' + DATA.pickup_week + ' <em>pickups</em>';
      renderFeatured();
      renderQueue();
      renderBoard();
    }
    const bootPromise = boot();

    /* ---------- matchup ---------- */""",
)

# --- 4. Auth bar above the header. ---
old = "    <header class=\"top\">"
assert old in src
src = src.replace(old, "    <div class=\"authbar\" id=\"authArea\" aria-label=\"Account\"></div>\n" + old, 1)

# --- 5. Save-matchup UI inside the matchup section. ---
old = '      <button class="btn primary" id="compareBtn">Compare teams</button>'
assert old in src
src = src.replace(
    old,
    old
    + """
      <div class="mu-save">
        <input id="muName" maxlength="120" placeholder="Name this matchup to save it" aria-label="Matchup name">
        <button class="btn" id="saveMatchupBtn">Save matchup</button>
      </div>
      <div id="savedMatchups" hidden>
        <h3>Saved matchups</h3>
        <div id="savedMatchupList"></div>
      </div>""",
    1,
)

# --- 6. Watchlist section after the summary grid. ---
old = """    </section>

    <section class="board" id="board">"""
assert old in src
src = src.replace(
    old,
    """    </section>

    <section class="watchlist-sec" id="watchlistSection" hidden aria-label="My watchlist">
      <div class="section-label"><b>My watchlist</b><span>Saved waiver targets</span></div>
      <div id="watchlist"></div>
    </section>

    <section class="board" id="board">""",
    1,
)

# --- 7. "Add to watchlist" button in the player drawer. ---
old = "        </table></div>`;"
assert old in src
src = src.replace(
    old,
    "        </table></div>` +\n        '<button class=\"btn wl-add\" data-name=\"' + esc(p.name) + '\">Add to watchlist</button>';",
    1,
)

# --- 8. Extra CSS for the account UI. ---
old = "  </style>"
assert old in src
src = src.replace(
    old,
    """    .authbar { display: flex; justify-content: flex-end; align-items: center; gap: 14px; padding: 10px clamp(20px, 5vw, 72px); font-size: 13px; color: var(--muted); border-bottom: 1px solid var(--line); }
    .authbar a { color: var(--text); text-decoration: none; border: 1px solid var(--line-strong); padding: 6px 14px; border-radius: 999px; }
    .authbar a:hover { border-color: var(--accent); }
    .authbar .linklike { background: none; border: 0; padding: 0; color: var(--muted); cursor: pointer; font: inherit; text-decoration: underline; }
    .mu-save { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
    .mu-save input { flex: 1; min-width: 200px; background: var(--bg); border: 1px solid var(--line-strong); color: var(--text); border-radius: 10px; padding: 10px 14px; font: inherit; }
    #savedMatchups { margin-top: 18px; }
    #savedMatchups h3 { font-size: 13px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 8px; }
    .saved-mu { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
    .saved-mu-load { background: none; border: 1px solid var(--line-strong); color: var(--text); border-radius: 8px; padding: 8px 12px; cursor: pointer; font: inherit; text-align: left; }
    .saved-mu-load:hover { border-color: var(--accent); }
    .saved-mu-del, .wl-del { background: none; border: 0; color: var(--muted); cursor: pointer; font-size: 18px; line-height: 1; padding: 4px 8px; }
    .saved-mu-del:hover, .wl-del:hover { color: var(--text); }
    .watchlist-sec { padding: 0 clamp(20px, 5vw, 72px); margin: 8px 0 28px; }
    .wl-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--line); }
    .wl-name { background: none; border: 0; color: var(--text); font: inherit; font-weight: 600; cursor: pointer; padding: 0; text-align: left; }
    .wl-name:hover { color: var(--accent); }
    .wl-sub { color: var(--muted); font-size: 13px; }
    .wl-score { margin-left: auto; font-weight: 700; color: var(--accent); }
    .wl-add { margin-top: 14px; }
  </style>""",
    1,
)

# --- 9. Second script: accounts, saved matchups, watchlist. ---
ACCOUNT_JS = """
  <script>
    /* Accounts, saved matchups, and the watchlist. Served by the API. */
    async function api(path, opts) {
      const r = await fetch(path, Object.assign({ headers: { 'Content-Type': 'application/json' } }, opts || {}));
      if (!r.ok) {
        let msg = 'Something went wrong';
        try { const j = await r.json(); if (j.detail) msg = j.detail; } catch (e) {}
        throw new Error(msg);
      }
      return r.status === 204 ? null : r.json();
    }

    let currentUser = null;

    async function initAuth() {
      const area = document.getElementById('authArea');
      try { currentUser = await api('/api/auth/me'); }
      catch (e) { currentUser = null; }
      if (currentUser) {
        area.innerHTML = '<span>Signed in as <b>' + esc(currentUser.email) + '</b></span>' +
          '<button class="linklike" id="logoutBtn">Log out</button>';
        document.getElementById('logoutBtn').addEventListener('click', async () => {
          await api('/api/auth/logout', { method: 'POST' });
          location.reload();
        });
        refreshSavedMatchups();
        refreshWatchlist();
      } else {
        area.innerHTML = '<a href="/login">Log in</a><a href="/signup">Sign up</a>';
      }
    }

    /* ----- saved matchups ----- */
    function currentRosters() {
      const lines = id => document.getElementById(id).value.split('\\n').map(s => s.trim()).filter(Boolean);
      return { a: lines('rosterA'), b: lines('rosterB') };
    }

    async function saveMatchup() {
      if (!currentUser) { location.href = '/login'; return; }
      const nameInput = document.getElementById('muName');
      const name = nameInput.value.trim();
      const rosters = currentRosters();
      if (!name) { showToast('Name the matchup first'); nameInput.focus(); return; }
      if (!rosters.a.length && !rosters.b.length) { showToast('Enter at least one player first'); return; }
      try {
        await api('/api/matchups', { method: 'POST', body: JSON.stringify({ name, roster_a: rosters.a, roster_b: rosters.b }) });
        nameInput.value = '';
        showToast('Matchup saved');
        refreshSavedMatchups();
      } catch (e) { showToast(e.message); }
    }

    async function refreshSavedMatchups() {
      const wrap = document.getElementById('savedMatchups');
      const list = document.getElementById('savedMatchupList');
      if (!currentUser) { wrap.hidden = true; return; }
      let items = [];
      try { items = await api('/api/matchups'); } catch (e) { return; }
      if (!items.length) { wrap.hidden = true; return; }
      wrap.hidden = false;
      list.innerHTML = items.map(m =>
        '<div class="saved-mu"><button class="saved-mu-load" data-id="' + m.id + '">' + esc(m.name) + '</button>' +
        '<button class="saved-mu-del" data-id="' + m.id + '" aria-label="Delete ' + esc(m.name) + '">\\u00d7</button></div>'
      ).join('');
    }

    document.getElementById('savedMatchupList').addEventListener('click', async e => {
      const load = e.target.closest('.saved-mu-load');
      const del = e.target.closest('.saved-mu-del');
      try {
        if (load) {
          const m = await api('/api/matchups/' + load.dataset.id);
          document.getElementById('rosterA').value = m.roster_a.join('\\n');
          document.getElementById('rosterB').value = m.roster_b.join('\\n');
          compareTeams();
          document.getElementById('matchup').scrollIntoView({ behavior: 'smooth' });
        } else if (del) {
          await api('/api/matchups/' + del.dataset.id, { method: 'DELETE' });
          refreshSavedMatchups();
          showToast('Deleted');
        }
      } catch (err) { showToast(err.message); }
    });
    document.getElementById('saveMatchupBtn').addEventListener('click', saveMatchup);

    /* ----- watchlist ----- */
    async function refreshWatchlist() {
      const sec = document.getElementById('watchlistSection');
      const list = document.getElementById('watchlist');
      if (!currentUser) { sec.hidden = true; return; }
      let items = [];
      try { items = await api('/api/watchlist'); } catch (e) { return; }
      sec.hidden = false;
      if (!items.length) {
        list.innerHTML = '<p class="mu-note">Nothing saved yet. Open any player and add them to your watchlist.</p>';
        return;
      }
      list.innerHTML = items.map(w => {
        const info = w.info || {};
        const sub = [info.position, info.team].filter(Boolean).join(' \\u00b7 ');
        const onBoard = info.source === 'board';
        return '<div class="wl-row">' +
          (onBoard
            ? '<button class="wl-name" data-name="' + esc(w.player_name) + '">' + esc(w.player_name) + '</button>'
            : '<span class="wl-name" style="cursor:default">' + esc(w.player_name) + '</span>') +
          (sub ? '<span class="wl-sub">' + esc(sub) + '</span>' : '') +
          (info.score != null ? '<span class="wl-score">' + Number(info.score).toFixed(1) + '</span>' : '') +
          '<button class="wl-del" data-name="' + esc(w.player_name) + '" aria-label="Remove ' + esc(w.player_name) + '">\\u00d7</button></div>';
      }).join('');
    }

    document.getElementById('watchlist').addEventListener('click', async e => {
      const nameBtn = e.target.closest('.wl-name[data-name]');
      const del = e.target.closest('.wl-del');
      if (nameBtn) { openDrawer(nameBtn.dataset.name); return; }
      if (del) {
        try {
          await api('/api/watchlist/' + encodeURIComponent(del.dataset.name), { method: 'DELETE' });
          refreshWatchlist();
          showToast('Removed');
        } catch (err) { showToast(err.message); }
      }
    });

    document.getElementById('drawerContent').addEventListener('click', async e => {
      const btn = e.target.closest('.wl-add');
      if (!btn) return;
      if (!currentUser) { location.href = '/login'; return; }
      try {
        await api('/api/watchlist', { method: 'POST', body: JSON.stringify({ player_name: btn.dataset.name }) });
        showToast('Added to your watchlist');
        refreshWatchlist();
      } catch (err) { showToast(err.message); }
    });

    initAuth();
  </script>"""

old = "  </script>\n</body>"
assert old in src
src = src.replace(old, "  </script>" + ACCOUNT_JS + "\n</body>", 1)

open(DST, "w").write(src)
print("wrote", DST, len(src), "chars")
