// puts the news headlines into <ul id="news">, links go to the official sites
(function () {
    var script = document.currentScript;
    var limit = +(script.dataset.limit || 6);
    var ul = document.getElementById('news');
    if (!ul) return;
    fetch(script.dataset.url).then(function (r) { return r.json(); }).then(function (data) {
        ul.innerHTML = '';
        if (!data.items.length) { ul.innerHTML = '<li class="muted small">No headlines right now.</li>'; return; }
        data.items.slice(0, limit).forEach(function (it) {
            var li = document.createElement('li'), a = document.createElement('a'), src = document.createElement('span');
            a.href = it.url; a.textContent = it.title; a.target = '_blank'; a.rel = 'noopener';
            src.className = 'src';
            src.textContent = it.source + (it.timestamp ? ' · ' + new Date(it.timestamp * 1000).toLocaleDateString() : '');
            li.appendChild(a); li.appendChild(src); ul.appendChild(li);
        });
    }).catch(function () {
        ul.innerHTML = '<li class="muted small">Couldn’t load headlines.</li>';
    });
})();
