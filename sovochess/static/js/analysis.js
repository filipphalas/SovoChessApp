// analysis board + prep
import * as T from './pgn-tree.js';

export function initAnalysis(Chess, page) {
    const $ = (id) => document.getElementById(id);
    const csrf = document.querySelector('meta[name=csrf-token]').content;

    let root = T.makeRoot();
    let cur = root;
    let headers = {};
    let result = '*';
    let dirty = false;
    let prepId = page.prep ? page.prep.id : null;

    // board

    const board = Chessboard('board', {
        position: 'start',
        draggable: true,
        pieceTheme: page.pieces + '{piece}.png',
        moveSpeed: 120,
        onDragStart,
        onDrop,
        onSnapEnd: () => board.position(cur.fen, false),
    });
    SovoBoardFit($('board-col'), $('board-stack'), $('board'), () => { board.resize(); decorate(); }, 30);

    function onDragStart(square, piece) {
        const turn = cur.fen.split(' ')[1];
        if (piece[0] !== turn) return false;
        new Chess(cur.fen).moves({ square, verbose: true }).forEach((m) => {
            $('board').querySelector('[data-square="' + m.to + '"]')?.classList.add('hint', ...(m.captured ? ['capture'] : []));
        });
    }

    function onDrop(from, to) {
        $('board').querySelectorAll('.hint').forEach((el) => el.classList.remove('hint', 'capture'));
        if (to === 'offboard' || from === to) return 'snapback';
        const legal = new Chess(cur.fen).moves({ square: from, verbose: true }).filter((m) => m.to === to);
        if (!legal.length) return 'snapback';
        if (legal.some((m) => m.promotion)) {
            choosePromotion(cur.fen.split(' ')[1]).then((p) => {
                if (p) play({ from, to, promotion: p }, true);
                else board.position(cur.fen, false);
            });
            return;
        }
        // dont animate, the piece is already there (animating made it look like it moved twice)
        play({ from, to }, false);
    }

    function play(move, animate = true) {
        const before = cur.children.length;
        const node = T.addMove(Chess, cur, move);
        if (!node) return false;
        if (cur.children.length !== before) markDirty();
        go(node, animate);
        return true;
    }

    function choosePromotion(color) {
        return new Promise((resolve) => {
            const box = $('promo-choices');
            box.innerHTML = '';
            for (const p of ['q', 'r', 'b', 'n']) {
                const b = document.createElement('button');
                b.type = 'button'; b.className = 'btn';
                b.innerHTML = '<img src="' + page.pieces + color + p.toUpperCase() + '.png" width="44" height="44" alt="' + p + '">';
                b.onclick = () => { closeModal('promo-modal'); resolve(p); };
                box.appendChild(b);
            }
            $('promo-modal').onclick = (e) => { if (e.target.id === 'promo-modal') { closeModal('promo-modal'); resolve(null); } };
            openModal('promo-modal');
        });
    }

    function decorate() {
        const el = $('board');
        el.querySelectorAll('.last-move, .check').forEach((s) => s.classList.remove('last-move', 'check'));
        if (cur.uci) {
            el.querySelector('[data-square="' + cur.uci.slice(0, 2) + '"]')?.classList.add('last-move');
            el.querySelector('[data-square="' + cur.uci.slice(2, 4) + '"]')?.classList.add('last-move');
        }
        const g = new Chess(cur.fen);
        if (g.inCheck()) {
            const k = g.board().flat().find((s) => s && s.type === 'k' && s.color === g.turn());
            if (k) el.querySelector('[data-square="' + k.square + '"]')?.classList.add('check');
        }
    }

    // navigation

    function go(node, animate = true) {
        cur = node;
        board.position(cur.fen, animate);
        setTimeout(decorate, animate ? 130 : 0);
        renderTree();
        $('move-comment').value = cur.comment || '';
        $('comment-target').textContent = cur.san ? T.moveNumber(cur) + ' ' + cur.san : 'the starting position';
        $('promote-btn').disabled = T.isMainline(cur);
        $('delete-btn').disabled = !cur.parent;
        engine.analyse(cur.fen);
    }

    document.querySelectorAll('[data-nav]').forEach((b) => b.addEventListener('click', () => nav(b.dataset.nav)));
    function nav(where) {
        if (where === 'start') go(root);
        else if (where === 'back' && cur.parent) go(cur.parent);
        else if (where === 'fwd' && cur.children.length) go(cur.children[0]);
        else if (where === 'end') go(T.mainlineEnd(cur));
    }

    document.addEventListener('keydown', (e) => {
        if (e.target.matches('input, textarea, select') || document.querySelector('.modal.open')) {
            if (e.key === 'Escape') document.querySelectorAll('.modal.open').forEach((m) => m.classList.remove('open'));
            return;
        }
        const map = { ArrowLeft: 'back', ArrowRight: 'fwd', Home: 'start', End: 'end' };
        if (map[e.key]) { nav(map[e.key]); e.preventDefault(); }
        else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            // up/down switches between side lines
            if (!cur.parent) return;
            const sibs = cur.parent.children, i = sibs.indexOf(cur);
            const j = e.key === 'ArrowUp' ? i - 1 : i + 1;
            if (sibs[j]) go(sibs[j]);
            e.preventDefault();
        } else if (e.key === 'f' || e.key === 'F') flip();
    });

    function flip() { board.flip(); decorate(); updateEvalBar(); }
    $('flip').addEventListener('click', flip);

    // tree rendering

    function esc(s) { return s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

    function moveHtml(node, forceNumber) {
        const num = T.isWhiteMove(node) || forceNumber ? '<span class="num">' + T.moveNumber(node) + '</span>' : '';
        let h = num + '<span class="mv' + (node === cur ? ' cur' : '') + '" data-id="' + node.id + '">' +
            esc(node.san) + T.nagSymbol(node.nag) + '</span> ';
        if (node.comment) h += '<span class="cmt">' + esc(node.comment) + '</span> ';
        return h;
    }

    function lineHtml(from, force) {
        let h = '', n = from;
        while (n.children.length) {
            const [main, ...sides] = n.children;
            h += moveHtml(main, force);
            for (const s of sides) h += '<span class="var">' + moveHtml(s, true) + lineHtml(s, !!s.comment) + '</span>';
            force = sides.length > 0 || !!main.comment;
            n = main;
        }
        return h;
    }

    function renderTree() {
        const tree = $('tree');
        let h = root.comment ? '<span class="cmt">' + esc(root.comment) + '</span> ' : '';
        h += lineHtml(root, true);
        tree.innerHTML = '<div class="main">' + (h || '<span class="empty-tree">No moves yet. Drag a piece to start.</span>') + '</div>';
        tree.querySelector('.mv.cur')?.scrollIntoView({ block: 'nearest' });
    }

    $('tree').addEventListener('click', (e) => {
        const mv = e.target.closest('.mv');
        if (mv) go(T.findById(root, +mv.dataset.id), false);
    });

    $('move-comment').addEventListener('input', (e) => {
        cur.comment = e.target.value.replace(/[{}]/g, '');
        markDirty();
        clearTimeout(renderTree.t);
        renderTree.t = setTimeout(() => { renderTree(); }, 400);
    });

    $('promote-btn').addEventListener('click', () => { if (T.promote(cur)) { markDirty(); go(cur, false); } });
    $('delete-btn').addEventListener('click', () => { if (cur.parent) { markDirty(); go(T.remove(cur), false); } });
    $('clear-board').addEventListener('click', () => {
        if (root.children.length && !confirmInline('clear-board', 'Click again to clear all moves')) return;
        loadTree(T.makeRoot(), {}, '*'); markDirty();
    });

    // click twice to confirm instead of a popup
    function confirmInline(id, text) {
        const b = $(id);
        if (b.dataset.armed) { delete b.dataset.armed; b.textContent = b.dataset.label; return true; }
        b.dataset.label = b.textContent; b.dataset.armed = '1'; b.textContent = text;
        setTimeout(() => { if (b.dataset.armed) { delete b.dataset.armed; b.textContent = b.dataset.label; } }, 3000);
        return false;
    }

    function loadTree(newRoot, newHeaders, newResult) {
        root = newRoot; headers = newHeaders || {}; result = newResult || '*';
        go(root, false);
    }

    // stockfish (runs in a web worker)

    const engine = (() => {
        let worker = null, ready = false, on = false, fen = null, lines = [], depth = 0, pending = null;

        function start() {
            if (worker) return;
            try { worker = new Worker(page.stockfish); }
            catch (e) { $('engine-lines').innerHTML = '<div class="line">Stockfish could not start in this browser.</div>'; return; }
            worker.onmessage = (e) => onLine(String(e.data));
            worker.onerror = () => { $('engine-lines').innerHTML = '<div class="line">Stockfish failed to load.</div>'; };
            send('uci');
            send('setoption name MultiPV value 3');
            send('isready');
        }
        function send(cmd) { worker && worker.postMessage(cmd); }

        function onLine(line) {
            if (line === 'readyok') { ready = true; if (pending) { const f = pending; pending = null; analyse(f); } return; }
            if (!line.startsWith('info') || !line.includes(' pv ')) return;
            const d = +(line.match(/ depth (\d+)/) || [])[1];
            const k = +((line.match(/ multipv (\d+)/) || [])[1] || 1);
            const cp = line.match(/ score cp (-?\d+)/), mate = line.match(/ score mate (-?\d+)/);
            const pv = line.split(' pv ')[1].trim().split(' ');
            const whiteToMove = fen.split(' ')[1] === 'w';
            const sign = whiteToMove ? 1 : -1;  // stockfish gives the score for the side to move, i want it for white
            const score = mate ? { mate: sign * +mate[1] } : { cp: sign * +(cp ? cp[1] : 0) };
            lines[k - 1] = { score, pv };
            depth = d;
            draw();
        }

        function analyse(newFen) {
            fen = newFen; lines = []; depth = 0;
            if (!on) return;
            if (!ready) { pending = newFen; return; }
            const g = new Chess(newFen);
            if (g.isGameOver()) {
                $('engine-lines').innerHTML = '<div class="line">' + (g.isCheckmate() ? 'Checkmate.' : 'Game over: draw.') + '</div>';
                setBar(g.isCheckmate() ? { mate: g.turn() === 'w' ? -0 : 0, winner: g.turn() === 'w' ? 'b' : 'w' } : { cp: 0 });
                return;
            }
            send('stop');
            send('position fen ' + newFen);
            send('go depth 22');
            $('engine-lines').innerHTML = '<div class="line muted">Thinking…</div>';
        }

        function fmt(score) {
            if (score.mate !== undefined) return (score.mate > 0 ? '#' : '#-') + Math.abs(score.mate);
            const v = score.cp / 100;
            return (v > 0 ? '+' : '') + v.toFixed(2);
        }

        function pvToSan(pv) {
            const g = new Chess(fen);
            const out = [];
            const [, turn, , , , num] = fen.split(' ');
            let n = +num, white = turn === 'w';
            for (const u of pv.slice(0, 10)) {
                let m;
                try { m = g.move({ from: u.slice(0, 2), to: u.slice(2, 4), promotion: u[4] }); } catch (e) { break; }
                if (white) out.push(n + '. ' + m.san);
                else out.push(out.length ? m.san : n + '... ' + m.san);
                if (!white) n++;
                white = !white;
            }
            return out.join(' ');
        }

        function draw() {
            const box = $('engine-lines');
            box.innerHTML = '';
            lines.forEach((l, i) => {
                if (!l) return;
                const div = document.createElement('div');
                div.className = 'line';
                div.title = 'Click to play ' + l.pv[0];
                div.innerHTML = '<b>' + fmt(l.score) + '</b> ' + esc(pvToSan(l.pv));
                div.onclick = () => { const u = l.pv[0]; play({ from: u.slice(0, 2), to: u.slice(2, 4), promotion: u[4] }); };
                box.appendChild(div);
                if (i === 0) setBar(l.score);
            });
            $('engine-depth').textContent = 'depth ' + depth;
        }

        function toggle(v) {
            on = v;
            $('eval-bar').classList.toggle('off', !on);
            if (on) { start(); analyse(cur.fen); }
            else {
                send('stop');
                $('engine-lines').innerHTML = '<div class="line muted">Engine off.</div>';
                $('engine-depth').textContent = '';
            }
        }
        return { analyse, toggle };
    })();

    let lastScore = { cp: 0 };
    function setBar(score) { lastScore = score; updateEvalBar(); }
    function updateEvalBar() {
        const s = lastScore;
        let pct;
        if (s.winner) pct = s.winner === 'w' ? 100 : 0;
        else if (s.mate !== undefined) pct = s.mate > 0 ? 100 : 0;
        else pct = 50 + 50 * (2 / (1 + Math.exp(-0.004 * s.cp)) - 1);  // so +4 is about 90% of the bar
        const flipped = board.orientation() === 'black';
        $('eval-white').style.height = (flipped ? 100 - pct : pct) + '%';
        $('eval-white').style.bottom = flipped ? 'auto' : '0';
        $('eval-white').style.top = flipped ? '0' : 'auto';
        const label = s.mate !== undefined && !s.winner ? 'M' + Math.abs(s.mate) : s.cp !== undefined ? Math.abs(s.cp / 100).toFixed(1) : '';
        const whiteBetter = pct >= 50;
        $('eval-top').textContent = (whiteBetter === flipped) ? label : '';
        $('eval-bottom').textContent = (whiteBetter !== flipped) ? label : '';
    }

    $('engine-on').addEventListener('change', (e) => {
        engine.toggle(e.target.checked);
        try { localStorage.setItem('sovo-engine', e.target.checked ? '1' : '0'); } catch (err) { /* private mode */ }
    });

    // pgn import

    let parsedGames = [];

    function readText(text) {
        $('import-error').hidden = true;
        $('game-pick-wrap').hidden = true;
        text = text.trim();
        if (!text) return showImportError('Paste a PGN or FEN first.');
        if (T.looksLikeFen(text)) {
            let fen;
            try { fen = new Chess(text.split(/\s+/).length < 6 ? completeFen(text) : text).fen(); }
            catch (e) { return showImportError('That FEN isn’t valid: ' + e.message); }
            loadTree(T.makeRoot(fen), {}, '*'); markDirty(); closeModal('import-modal');
            return;
        }
        parsedGames = T.splitGames(text);
        if (!parsedGames.length) return showImportError('No games found in that text.');
        if (parsedGames.length === 1) return openGame(parsedGames[0]);
        showGamePicker();
    }

    function completeFen(text) {
        const p = text.trim().split(/\s+/);
        return [p[0], p[1] || 'w', p[2] || '-', p[3] || '-', p[4] || '0', p[5] || '1'].join(' ');
    }

    function openGame(g) {
        const parsed = T.parseGame(Chess, g);
        if (!parsed.root.children.length && parsed.error) return showImportError(parsed.error);
        loadTree(parsed.root, parsed.headers, parsed.result);
        markDirty();
        const titleEl = $('prep-title');
        if (titleEl && !titleEl.value) {
            const h = parsed.headers;
            titleEl.value = h.Opening || (h.White && h.Black ? h.White + ' – ' + h.Black : '') || h.Event || '';
        }
        closeModal('import-modal');
        if (parsed.error) flash(parsed.error);
    }

    function showGamePicker() {
        const pick = $('game-pick');
        pick.innerHTML = '';
        $('game-count').textContent = parsedGames.length + ' games found.';
        parsedGames.slice(0, 500).forEach((g, i) => {
            const h = g.headers;
            const b = document.createElement('button');
            b.type = 'button';
            b.textContent = (i + 1) + '. ' + (h.White || '?') + ' – ' + (h.Black || '?') + '  ' + (h.Result || '') +
                (h.Event && h.Event !== '?' ? '  · ' + h.Event : '') + (h.Date ? '  · ' + h.Date : '');
            b.onclick = () => openGame(g);
            pick.appendChild(b);
        });
        $('game-pick-wrap').hidden = false;
    }

    function showImportError(msg) { $('import-error').textContent = msg; $('import-error').hidden = false; }

    $('open-import').addEventListener('click', () => {
        $('import-error').hidden = true; $('game-pick-wrap').hidden = true; openModal('import-modal');
        setTimeout(() => $('pgn-text').focus(), 50);
    });
    $('load-text').addEventListener('click', () => readText($('pgn-text').value));

    function readFile(file) {
        if (!file) return;
        if (file.size > 20 * 1024 * 1024) return showImportError('That file is over 20 MB. Please split it up first.');
        const r = new FileReader();
        r.onload = () => { $('pgn-text').value = r.result.length < 200000 ? r.result : ''; readText(r.result); };
        r.onerror = () => showImportError('Couldn’t read that file.');
        r.readAsText(file);
    }
    $('pgn-file').addEventListener('change', (e) => readFile(e.target.files[0]));

    const dz = $('dropzone');
    ['dragenter', 'dragover'].forEach((t) => dz.addEventListener(t, (e) => { e.preventDefault(); dz.classList.add('over'); }));
    ['dragleave', 'drop'].forEach((t) => dz.addEventListener(t, (e) => { e.preventDefault(); dz.classList.remove('over'); }));
    dz.addEventListener('drop', (e) => readFile(e.dataTransfer.files[0]));
    // can drop a file anywhere on the page
    document.addEventListener('dragover', (e) => { if (e.dataTransfer?.types?.includes('Files')) e.preventDefault(); });
    document.addEventListener('drop', (e) => {
        if (e.target.closest('#dropzone')) return;
        if (e.dataTransfer?.files?.length) { e.preventDefault(); openModal('import-modal'); readFile(e.dataTransfer.files[0]); }
    });

    $('import-all')?.addEventListener('click', () => {
        const btn = $('import-all');
        const games = parsedGames.slice(0, 500).map((g) => {
            const p = T.parseGame(Chess, g);
            const uci = [];
            for (let n = p.root; n.children.length && uci.length < 20; n = n.children[0]) uci.push(n.children[0].uci);
            const pgn = (Object.entries(g.headers).map(([k, v]) => '[' + k + ' "' + v.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"]').join('\n') +
                '\n\n' + g.movetext.trim()).trim();
            return { pgn, headers: g.headers, uci: uci.join(' '), plies: T.countPlies(p.root) };
        });
        btn.disabled = true; btn.textContent = 'Importing…';
        postJson(page.urls.libraryImport, { games, new_collection: $('import-collection').value.trim() })
            .then((d) => {
                if (d.error) throw new Error(d.error);
                window.location = page.urls.library + (d.collection_id ? '?collection=' + d.collection_id : '');
            })
            .catch((e) => { showImportError(e.message || 'Import failed.'); btn.disabled = false; btn.textContent = 'Import all to library'; });
    });

    // export

    function currentPgn() {
        const h = { ...headers };
        if ($('prep-title')) {
            h.Event = $('prep-title').value.trim() || h.Event || 'SovoChess analysis';
            const side = $('prep-side').value, opp = $('prep-opponent').value.trim();
            if (opp) { if (side === 'w') h.Black = opp; else h.White = opp; }
        }
        return T.toPgn(root, h, result);
    }

    $('copy-pgn').addEventListener('click', () => {
        navigator.clipboard.writeText(currentPgn()).then(() => flash('PGN copied.'), () => flash('Couldn’t copy. Use Download instead.'));
    });
    $('download-pgn').addEventListener('click', () => {
        const name = (($('prep-title') && $('prep-title').value) || 'analysis').replace(/[^\w-]+/g, '-').replace(/^-|-$/g, '') || 'analysis';
        const blob = new Blob([currentPgn()], { type: 'application/x-chess-pgn' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob); a.download = name + '.pgn';
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    });

    // saving

    function postJson(url, data) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify(data),
        }).then((r) => r.json().catch(() => ({ error: 'Server error (' + r.status + ').' })));
    }

    function markDirty() {
        if (!page.loggedIn) return;
        dirty = true;
        $('save-state').textContent = 'Unsaved changes';
        $('save-state').classList.add('dirty');
    }
    function markSaved(text) {
        dirty = false;
        $('save-state').textContent = text;
        $('save-state').classList.remove('dirty');
    }
    ['prep-title', 'prep-opponent', 'prep-notes', 'prep-side', 'game-notes', 'game-collection'].forEach((id) => {
        $(id)?.addEventListener('input', markDirty);
    });
    $('prep-side')?.addEventListener('change', (e) => {
        if ((e.target.value === 'b') !== (board.orientation() === 'black')) flip();
    });
    window.addEventListener('beforeunload', (e) => { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
    $('delete-prep-form')?.addEventListener('submit', (e) => {
        if (!confirmInline('delete-prep-form-btn', 'Click again to delete')) e.preventDefault(); else dirty = false;
    });
    const delBtn = $('delete-prep-form')?.querySelector('button');
    if (delBtn) delBtn.id = 'delete-prep-form-btn';

    function savePrep(asNew) {
        const title = $('prep-title') ? $('prep-title').value.trim() : '';
        const data = {
            id: asNew ? null : prepId,
            title: title || (headers.Opening || 'Untitled preparation'),
            side: $('prep-side') ? $('prep-side').value : (board.orientation() === 'black' ? 'b' : 'w'),
            opponent: $('prep-opponent') ? $('prep-opponent').value : '',
            notes: $('prep-notes') ? $('prep-notes').value : '',
            pgn: currentPgn(),
            start_fen: root.fen === T.START_FEN ? '' : root.fen,
        };
        $('save-btn').disabled = true;
        return postJson(page.urls.prepSave, data).then((d) => {
            $('save-btn').disabled = false;
            if (d.error) { flash(d.error); return; }
            if (asNew) { dirty = false; window.location = d.url; return; }
            prepId = d.id;
            markSaved('Saved ' + d.updated);
            history.replaceState(null, '', d.url);
            upsertPrepList(d, data.side);
        }).catch(() => { $('save-btn').disabled = false; flash('Couldn’t reach the server. Your changes are still here, try again.'); });
    }

    function upsertPrepList(d, side) {
        const list = $('prep-list');
        if (!list) return;
        $('prep-empty')?.remove();
        let a = list.querySelector('a[href="' + d.url + '"]');
        if (!a) {
            const li = document.createElement('li');
            a = document.createElement('a');
            a.href = d.url;
            li.appendChild(a);
            list.prepend(li);
        }
        list.querySelectorAll('a.active').forEach((x) => x.classList.remove('active'));
        a.className = 'active';
        a.innerHTML = '<span class="side-dot ' + side + '"></span>' + esc(d.title) + '<small>just now</small>';
    }

    function saveGameNotes() {
        const fd = new FormData();
        fd.append('notes', $('game-notes').value);
        fd.append('collection', $('game-collection').value);
        $('save-btn').disabled = true;
        fetch(page.game.saveUrl, { method: 'POST', headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'fetch' }, body: fd })
            .then((r) => r.json())
            .then(() => markSaved('Saved'))
            .catch(() => flash('Couldn’t save. Try again.'))
            .finally(() => { $('save-btn').disabled = false; });
    }

    $('save-btn')?.addEventListener('click', () => (page.mode === 'game' ? saveGameNotes() : savePrep(false)));
    $('to-prep-btn')?.addEventListener('click', () => savePrep(true));
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's' && $('save-btn')) { e.preventDefault(); $('save-btn').click(); }
    });

    // popups etc

    function openModal(id) { $(id).classList.add('open'); }
    function closeModal(id) { $(id).classList.remove('open'); }
    document.querySelectorAll('.modal [data-close]').forEach((b) => b.addEventListener('click', () => b.closest('.modal').classList.remove('open')));
    $('import-modal').addEventListener('click', (e) => { if (e.target.id === 'import-modal') closeModal('import-modal'); });

    function flash(text) {
        const el = $('save-state');
        const old = el.textContent;
        el.textContent = text;
        setTimeout(() => { if (el.textContent === text) el.textContent = old; }, 4000);
    }

    // start up

    const initial = page.prep || page.game;
    if (initial && initial.pgn) {
        const games = T.splitGames(initial.pgn);
        const parsed = games.length ? T.parseGame(Chess, games[0]) : null;
        if (parsed) loadTree(parsed.root, parsed.headers, parsed.result);
        else loadTree(T.makeRoot(), {}, '*');
        if (parsed && parsed.error) flash(parsed.error);
    } else if (page.prep && page.prep.startFen) {
        loadTree(T.makeRoot(page.prep.startFen), {}, '*');
    } else {
        loadTree(T.makeRoot(), {}, '*');
    }
    if (page.prep && page.prep.side === 'b') flip();

    let engineOn = false;
    try { engineOn = localStorage.getItem('sovo-engine') === '1'; } catch (e) { /* ignore */ }
    if (engineOn) { $('engine-on').checked = true; engine.toggle(true); }
}
