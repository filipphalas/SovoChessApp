// move tree with side lines + reading/writing pgn (no html stuff in here so i can test it with node)
// node = { id, san, uci, fen, comment, nag, parent, children }
// children[0] is the main line, the others are side lines. root has no move, just the start fen

export const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const NAG_TO_SYMBOL = { 1: '!', 2: '?', 3: '!!', 4: '??', 5: '!?', 6: '?!' };
const SYMBOL_TO_NAG = { '!': 1, '?': 2, '!!': 3, '??': 4, '!?': 5, '?!': 6 };
const RESULTS = new Set(['1-0', '0-1', '1/2-1/2', '*']);

let nextId = 1;

export function makeRoot(fen = START_FEN) {
    return { id: nextId++, san: null, uci: null, fen, comment: '', nag: 0, parent: null, children: [] };
}

// adds a move after node, if that move is already there it just returns it
export function addMove(Chess, node, move) {
    const game = new Chess(node.fen);
    let mv;
    try { mv = game.move(move); } catch (e) { return null; }
    const uci = mv.from + mv.to + (mv.promotion || '');
    const existing = node.children.find((c) => c.uci === uci);
    if (existing) return existing;
    const child = { id: nextId++, san: mv.san, uci, fen: game.fen(), comment: '', nag: 0, parent: node, children: [] };
    node.children.push(child);
    return child;
}

export function mainlineEnd(node) {
    while (node.children.length) node = node.children[0];
    return node;
}

export function pathTo(node) {
    const path = [];
    for (let n = node; n.parent; n = n.parent) path.unshift(n);
    return path;
}

export function isMainline(node) {
    for (let n = node; n.parent; n = n.parent) if (n.parent.children[0] !== n) return false;
    return true;
}

// makes the side line the main line
export function promote(node) {
    let n = node;
    while (n.parent && n.parent.children[0] === n) n = n.parent;
    if (!n.parent) return false;
    const sibs = n.parent.children;
    sibs.splice(sibs.indexOf(n), 1);
    sibs.unshift(n);
    return true;
}

// deletes node and everything after it
export function remove(node) {
    if (!node.parent) { node.children = []; return node; }
    const sibs = node.parent.children;
    sibs.splice(sibs.indexOf(node), 1);
    return node.parent;
}

export function findById(root, id) {
    const stack = [root];
    while (stack.length) {
        const n = stack.pop();
        if (n.id === id) return n;
        stack.push(...n.children);
    }
    return null;
}

export function countPlies(root) {
    let n = 0;
    for (let x = root; x.children.length; x = x.children[0]) n++;
    return n;
}

// move numbers

// "12." for white or "12..." for black
export function moveNumber(node) {
    const parts = node.parent.fen.split(' ');
    return parts[5] + (parts[1] === 'w' ? '.' : '...');
}

export function isWhiteMove(node) {
    return node.parent.fen.split(' ')[1] === 'w';
}

// writing pgn

function escapeComment(text) {
    return text.replace(/[{}]/g, '');
}

export function movetext(root) {
    const out = [];
    if (root.comment) out.push('{' + escapeComment(root.comment) + '}');

    function token(node, forceNumber) {
        const prefix = isWhiteMove(node) ? moveNumber(node) + ' ' : forceNumber ? moveNumber(node) + ' ' : '';
        let t = prefix + node.san + (node.nag ? NAG_TO_SYMBOL[node.nag] || ' $' + node.nag : '');
        if (node.comment) t += ' {' + escapeComment(node.comment) + '}';
        return t;
    }

    function line(from, force) {
        let n = from;
        while (n.children.length) {
            const [main, ...sides] = n.children;
            out.push(token(main, force));
            for (const side of sides) {
                out.push('(' + token(side, true));
                line(side, !!side.comment);
                out[out.length - 1] += ')';
            }
            force = sides.length > 0 || !!main.comment;
            n = main;
        }
    }
    line(root, true);
    return out.join(' ');
}

export function toPgn(root, headers = {}, result = '*') {
    const h = { Event: '?', Site: 'SovoChess', Date: '????.??.??', Round: '-', White: '?', Black: '?', Result: result, ...headers };
    h.Result = result;
    if (root.fen !== START_FEN) { h.SetUp = '1'; h.FEN = root.fen; } else { delete h.SetUp; delete h.FEN; }
    const tags = Object.entries(h)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => '[' + k + ' "' + String(v).replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"]');
    // max ~80 chars per line
    const words = (movetext(root) + ' ' + result).trim().split(' ');
    const lines = [];
    let cur = '';
    for (const w of words) {
        if (cur && cur.length + 1 + w.length > 80) { lines.push(cur); cur = w; }
        else cur = cur ? cur + ' ' + w : w;
    }
    if (cur) lines.push(cur);
    return tags.join('\n') + '\n\n' + lines.join('\n') + '\n';
}

// reading pgn

// splits a pgn file into separate games
export function splitGames(text) {
    const games = [];
    let cur = null;
    let inMoves = false;
    text = text.replace(/^﻿/, '').replace(/\r\n?/g, '\n');
    for (const raw of text.split('\n')) {
        const line = raw.trim();
        const tag = line.match(/^\[(\w+)\s+"((?:[^"\\]|\\.)*)"\]$/);
        if (tag) {
            if (!cur || inMoves) { cur = { headers: {}, movetext: '' }; games.push(cur); inMoves = false; }
            cur.headers[tag[1]] = tag[2].replace(/\\(.)/g, '$1');
        } else if (line) {
            if (!cur) { cur = { headers: {}, movetext: '' }; games.push(cur); }
            if (!line.startsWith('%')) { cur.movetext += line + '\n'; inMoves = true; }
        }
    }
    return games.filter((g) => g.movetext.trim() || Object.keys(g.headers).length);
}

const TOKEN_RE = /\{[^}]*\}|;[^\n]*|\$\d+|\(|\)|[^\s(){};]+/g;

// one game -> move tree
export function parseGame(Chess, game) {
    const headers = game.headers || {};
    let startFen = START_FEN;
    if (headers.FEN) {
        try { startFen = new Chess(headers.FEN).fen(); } catch (e) { return { root: makeRoot(), headers, result: '*', error: 'The FEN tag in this game is not valid.' }; }
    }
    const root = makeRoot(startFen);
    let cur = root;  // last move added
    const stack = [];  // where to go back to after a side line ends
    let result = headers.Result || '*';
    let error = null;
    let skipDepth = 0;  // skip the rest of a line after an illegal move

    for (const tok of game.movetext.match(TOKEN_RE) || []) {
        if (tok === '(') {
            if (skipDepth) { skipDepth++; continue; }
            stack.push(cur);
            cur = cur.parent || cur;  // side line is instead of the last move
            continue;
        }
        if (tok === ')') {
            if (skipDepth) { skipDepth--; if (skipDepth) continue; }
            if (stack.length) cur = stack.pop();
            continue;
        }
        if (skipDepth) continue;
        if (tok[0] === '{' || tok[0] === ';') {
            const text = (tok[0] === '{' ? tok.slice(1, -1) : tok.slice(1)).replace(/\s+/g, ' ').trim();
            // remove stuff like [%clk 0:03:00] that lichess/chess.com add
            const clean = text.replace(/\[%[^\]]*\]/g, '').trim();
            if (clean) cur.comment = cur.comment ? cur.comment + ' ' + clean : clean;
            continue;
        }
        if (tok[0] === '$') { if (cur !== root) cur.nag = +tok.slice(1); continue; }
        if (RESULTS.has(tok)) { if (!stack.length) result = tok; continue; }

        let san = tok.replace(/^\d+\.+/, '');  // remove move numbers
        if (!san || /^\d+$/.test(san)) continue;
        const ann = san.match(/[!?]+$/);
        if (ann) san = san.slice(0, -ann[0].length);
        san = san.replace(/^0-0-0/, 'O-O-O').replace(/^0-0/, 'O-O').replace(/[+#]$/, '');
        if (!san) continue;

        const child = addMove(Chess, cur, san);
        if (!child) {
            error = error || `Stopped reading at "${tok}" after ${pathTo(cur).length} moves: that move isn't legal there.`;
            if (stack.length) { skipDepth = 1; } else { break; }
            continue;
        }
        if (ann && SYMBOL_TO_NAG[ann[0]]) child.nag = SYMBOL_TO_NAG[ann[0]];
        cur = child;
    }
    return { root, headers, result, error };
}

export function nagSymbol(nag) {
    return NAG_TO_SYMBOL[nag] || '';
}

// is it a fen or a pgn
export function looksLikeFen(text) {
    return /^\s*([1-8pnbrqkPNBRQK]+\/){7}[1-8pnbrqkPNBRQK]+(\s+[wb](\s+\S+){0,4})?\s*$/.test(text);
}
