// boards inside the guides, they start playing the moves when you scroll to them
export function initArticleBoards(Chess, pieceBase) {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    document.querySelectorAll('.article-board').forEach((fig) => {
        const startFen = fig.dataset.fen || new Chess().fen();
        const sans = (fig.dataset.moves || '').split(/\s+/).filter(Boolean);

        // work out every position first so going back/forward is instant
        const game = new Chess(startFen);
        const fens = [game.fen()];
        const labels = [''];
        const lastMoves = [null];
        for (const san of sans) {
            const before = fens[fens.length - 1].split(' ');
            let mv;
            try { mv = game.move(san); } catch (e) { break; }
            fens.push(game.fen());
            labels.push(before[5] + (before[1] === 'w' ? '. ' : '... ') + mv.san);
            lastMoves.push([mv.from, mv.to]);
        }

        const boardEl = fig.querySelector('.ab-board');
        const board = Chessboard(boardEl, {
            position: startFen.split(' ')[0],
            orientation: fig.dataset.orientation === 'black' ? 'black' : 'white',
            pieceTheme: pieceBase + '{piece}.png',
            moveSpeed: 260,
        });

        let ply = 0, timer = null;
        const playBtn = fig.querySelector('[data-act=play]');
        const label = fig.querySelector('.ab-move');
        const bar = fig.querySelector('.ab-progress i');

        function mark() {
            boardEl.querySelectorAll('.last-move').forEach((el) => el.classList.remove('last-move'));
            const lm = lastMoves[ply];
            if (lm) lm.forEach((sq) => boardEl.querySelector('[data-square="' + sq + '"]')?.classList.add('last-move'));
        }

        let lastWidth = 0;
        new ResizeObserver(() => {
            if (boardEl.clientWidth === lastWidth) return;
            lastWidth = boardEl.clientWidth;
            board.resize(); mark();
        }).observe(boardEl);

        function stop() {
            clearInterval(timer); timer = null;
            if (playBtn) { playBtn.innerHTML = '&#x25B6;'; playBtn.setAttribute('aria-label', 'Play'); }
        }

        function go(n, animate = true) {
            ply = Math.max(0, Math.min(fens.length - 1, n));
            board.position(fens[ply].split(' ')[0], animate);
            if (label) label.textContent = ply ? labels[ply] : 'Start';
            if (bar) bar.style.width = (fens.length > 1 ? (ply / (fens.length - 1)) * 100 : 0) + '%';
            setTimeout(mark, animate ? 270 : 0);
            if (ply === fens.length - 1) stop();
        }

        function play() {
            if (fens.length < 2) return;
            if (ply === fens.length - 1) go(0, false);
            if (playBtn) { playBtn.innerHTML = '&#x275A;&#x275A;'; playBtn.setAttribute('aria-label', 'Pause'); }
            timer = setInterval(() => go(ply + 1), 1100);
        }

        fig.querySelectorAll('[data-act]').forEach((btn) => btn.addEventListener('click', () => {
            const act = btn.dataset.act;
            if (act === 'play') { timer ? stop() : play(); return; }
            stop();
            if (act === 'start') go(0);
            else if (act === 'back') go(ply - 1);
            else if (act === 'fwd') go(ply + 1);
            else if (act === 'end') go(fens.length - 1);
        }));

        go(0, false);

        // autoplay once when most of the board is visible
        if (fens.length > 1 && !reduced && 'IntersectionObserver' in window) {
            const io = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) { io.disconnect(); setTimeout(play, 500); }
            }, { threshold: 0.7 });
            io.observe(boardEl);
        }
    });
}
