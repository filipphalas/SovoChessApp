// makes the board as big as the column but always a multiple of 8px so theres no gap on the side
// (the css already stops the column from being taller than the screen)
window.SovoBoardFit = function (column, stack, boardEl, onResize, reserve) {
    var last = 0;
    function apply() {
        var size = Math.max(208, Math.floor((column.clientWidth - (reserve || 0)) / 8) * 8);
        if (size === last) return;
        last = size;
        stack.style.width = (size + (reserve || 0)) + 'px';
        boardEl.style.width = (size + 1) + 'px';  // +1 bc chessboard.js takes 1px off
        boardEl.style.marginRight = '-1px';
        if (onResize) onResize(size);
    }
    if ('ResizeObserver' in window) new ResizeObserver(apply).observe(column);
    else window.addEventListener('resize', apply);
    apply();
};
