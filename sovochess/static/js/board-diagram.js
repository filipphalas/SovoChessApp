// small static boards for thumbnails: <div class="mini-board" data-fen="...">
(function () {
    var base = document.currentScript.dataset.pieces;
    document.querySelectorAll('.mini-board[data-fen]').forEach(function (el) {
        var rows = (el.dataset.fen || '').split(' ')[0].split('/');
        if (rows.length !== 8) return;
        var html = '';
        rows.forEach(function (row, r) {
            var c = 0;
            row.split('').forEach(function (ch) {
                if (/\d/.test(ch)) {
                    for (var i = 0; i < +ch; i++, c++) html += '<i class="' + ((r + c) % 2 ? 'd' : 'l') + '"></i>';
                } else {
                    var code = (ch === ch.toUpperCase() ? 'w' : 'b') + ch.toUpperCase();
                    html += '<i class="' + ((r + c) % 2 ? 'd' : 'l') + '" style="background-image:url(' + base + code + '.png)"></i>';
                    c++;
                }
            });
        });
        el.innerHTML = html;
        el.setAttribute('role', 'img');
    });
})();
