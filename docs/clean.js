/* Tidywells file cleaner. Mirrors src/tidywells/loaders.py (read_volumetrics, read_bc_production).
   Runs in the browser; nothing is uploaded. Also loads in Node for the parity test (tests/test_clean_js.py). */
(function (root) {
  "use strict";
  // strings pandas reads as missing by default; used where the Python loader tests for a missing value
  var NA = {"": 1, "#N/A": 1, "#N/A N/A": 1, "#NA": 1, "-1.#IND": 1, "-1.#QNAN": 1, "-NaN": 1, "-nan": 1, "1.#IND": 1, "1.#QNAN": 1,
    "<NA>": 1, "N/A": 1, "NA": 1, "NULL": 1, "NaN": 1, "None": 1, "n/a": 1, "nan": 1, "null": 1};

  function splitLine(line) {
    if (line.indexOf('"') < 0) return line.split(",");
    var out = [], cur = "", q = false;
    for (var i = 0; i < line.length; i++) {
      var c = line.charAt(i);
      if (q) {
        if (c === '"') { if (line.charAt(i + 1) === '"') { cur += '"'; i++; } else q = false; }
        else cur += c;
      } else if (c === '"') q = true;
      else if (c === ",") { out.push(cur); cur = ""; }
      else cur += c;
    }
    out.push(cur);
    return out;
  }

  // Streaming CSV reader: feed(text) any number of times, then end(). onRow gets an array of fields.
  function CsvReader(onRow) { this.onRow = onRow; this.left = ""; this.pending = null; }
  CsvReader.prototype.feed = function (text) {
    var s = this.left + text, start = 0, nl;
    while ((nl = s.indexOf("\n", start)) >= 0) {
      this._line(s.slice(start, nl)); start = nl + 1;
    }
    this.left = s.slice(start);
  };
  CsvReader.prototype._line = function (line) {
    if (line.charCodeAt(line.length - 1) === 13) line = line.slice(0, -1);
    if (this.pending !== null) line = this.pending + "\n" + line;
    if (line.indexOf('"') >= 0) {
      var n = 0, k = -1;
      while ((k = line.indexOf('"', k + 1)) >= 0) n++;
      if (n % 2) { this.pending = line; return; }
    }
    this.pending = null;
    if (line === "") return;
    this.onRow(splitLine(line));
  };
  CsvReader.prototype.end = function () {
    if (this.left !== "" || this.pending !== null) { var l = this.left; this.left = ""; this._line(l); }
  };

  function num(s) {
    if (s === undefined) return null;
    s = s.trim();
    if (s === "" || NA[s]) return null;
    var v = Number(s);
    return isNaN(v) ? null : v;
  }
  function esc(v) {
    if (v === null || v === undefined) return "";
    v = String(v);
    return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }

  // ---- Petrinex Conventional Volumetrics (Alberta, Saskatchewan) ----
  function VolCleaner(opts) {
    opts = opts || {};
    this.products = opts.products || ["OIL", "GAS", "COND"];
    this.activity = opts.activity || "PROD";
    this.rows = []; this.stats = {read: 0, kept: 0, masked: 0};
    this.idx = null;
  }
  VolCleaner.kind = "volumetrics";
  VolCleaner.detect = function (header) { return header.indexOf("ProductionMonth") >= 0 && header.indexOf("FromToID") >= 0; };
  VolCleaner.prototype.row = function (r) {
    if (!this.idx) {
      var h = {}; for (var i = 0; i < r.length; i++) h[r[i].trim()] = i;
      this.idx = h; return;
    }
    var x = this.idx, st = this.stats; st.read++;
    if (r[x.ActivityID] !== this.activity || r[x.FromToIDType] !== "WI" || this.products.indexOf(r[x.ProductID]) < 0) return;
    if (r[x.FromToID] === "***") { st.masked++; return; }
    var vol = num(r[x.Volume]), hrs = num(r[x.Hours]), pp = r[x.ProrationProduct];
    var id = r[x.FromToID];
    this.rows.push([r[x.ProductionMonth], id, id.slice(0, 2), r[x.ProductID], vol, hrs,
      !(pp === undefined || NA[pp]), r[x.ReportingFacilityID], r[x.OperatorBAID], r[x.OperatorName]]);
    st.kept++;
  };
  VolCleaner.header = ["month", "well_id", "province", "product", "volume", "hours", "prorated", "facility_id", "operator_code", "operator_name"];
  VolCleaner.prototype.finish = function () { return {header: VolCleaner.header, rows: this.rows, stats: this.stats}; };

  // ---- BC Energy Regulator production (zone_prd*.csv) ----
  var BC = [["GAS", "Gas_prod_vol (e3m3)"], ["OIL", "Oil_prod_vol (m3)"], ["COND", "Cond_prod_vol (m3)"], ["WATER", "Water_prod_vol (m3)"]];
  function BcCleaner(opts) {
    opts = opts || {};
    this.products = opts.products || ["OIL", "GAS", "COND"];
    this.skipped = false; this.idx = null; this.agg = {}; this.stats = {read: 0, kept: 0, masked: 0};
  }
  BcCleaner.kind = "bc";
  BcCleaner.detect = function (header) { return header.indexOf("UWI") >= 0 && header.indexOf("Prod_period") >= 0; };
  BcCleaner.prototype.row = function (r) {
    if (!this.skipped) { this.skipped = true; if (BcCleaner.detect(r.map(function (s) { return s.trim(); }))) { this.row(r); } return; }
    if (!this.idx) {
      var h = {}; for (var i = 0; i < r.length; i++) h[r[i].trim()] = i;
      this.idx = h; return;
    }
    var x = this.idx, st = this.stats; st.read++;
    var per = r[x.Prod_period].trim(), uwi = r[x.UWI].trim();
    var month = per.slice(0, 4) + "-" + per.slice(4, 6);
    var days = num(r[x.Prod_days]);
    for (var p = 0; p < BC.length; p++) {
      var prod = BC[p][0], col = x[BC[p][1]];
      if (this.products.indexOf(prod) < 0 || col === undefined) continue;
      var key = prod + "\t" + uwi + "\t" + month;
      var a = this.agg[key];
      if (!a) a = this.agg[key] = [0, null];
      var v = num(r[col]); if (v !== null) a[0] += v;
      if (days !== null && (a[1] === null || days > a[1])) a[1] = days;
    }
  };
  BcCleaner.header = ["month", "well_id", "province", "product", "volume", "days"];
  BcCleaner.prototype.finish = function () {
    var out = [], keys = Object.keys(this.agg), order = {GAS: 0, OIL: 1, COND: 2, WATER: 3};
    keys.sort(function (a, b) {
      var pa = a.split("\t"), pb = b.split("\t");
      if (order[pa[0]] !== order[pb[0]]) return order[pa[0]] - order[pb[0]];
      if (pa[1] !== pb[1]) return pa[1] < pb[1] ? -1 : 1;
      return pa[2] < pb[2] ? -1 : pa[2] > pb[2] ? 1 : 0;
    });
    for (var i = 0; i < keys.length; i++) {
      var p = keys[i].split("\t"), a = this.agg[keys[i]];
      out.push([p[2], p[1], "BC", p[0], a[0], a[1]]);
    }
    this.stats.kept = out.length;
    return {header: BcCleaner.header, rows: out, stats: this.stats};
  };

  function toCsv(res) {
    var lines = [res.header.join(",")];
    for (var i = 0; i < res.rows.length; i++) {
      var r = res.rows[i], o = [];
      for (var j = 0; j < r.length; j++) {
        var v = r[j];
        o.push(typeof v === "boolean" ? (v ? "True" : "False") : esc(v));
      }
      lines.push(o.join(","));
    }
    return lines.join("\n") + "\n";
  }

  // Detect the file type from its first rows and return a cleaner.
  function sniff(firstText, opts) {
    var lines = firstText.split("\n").slice(0, 3).map(function (l) { return splitLine(l.replace(/\r$/, "")).map(function (s) { return s.trim(); }); });
    for (var i = 0; i < lines.length; i++) {
      if (VolCleaner.detect(lines[i])) return new VolCleaner(opts);
      if (BcCleaner.detect(lines[i])) return new BcCleaner(opts);
    }
    return null;
  }

  // ---- browser only: read a .csv or a single-file .zip as a text stream, without loading it all ----
  function u32(b, o) { return (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0; }
  function u16(b, o) { return b[o] | (b[o + 1] << 8); }
  async function zipEntryStream(file) {
    var tail = new Uint8Array(await file.slice(Math.max(0, file.size - 70000)).arrayBuffer()), e = -1;
    for (var i = tail.length - 22; i >= 0; i--) if (tail[i] === 0x50 && tail[i + 1] === 0x4b && tail[i + 2] === 5 && tail[i + 3] === 6) { e = i; break; }
    if (e < 0) throw new Error("This does not look like a valid zip file.");
    var n = u16(tail, e + 10), cdSize = u32(tail, e + 12) >>> 0, cdOff = u32(tail, e + 16) >>> 0;
    if (cdOff === 0xffffffff) throw new Error("Zip64 files are not supported. Unzip the file and drop the .csv instead.");
    var cd = new Uint8Array(await file.slice(cdOff, cdOff + cdSize).arrayBuffer()), p = 0, found = null;
    for (var k = 0; k < n; k++) {
      var method = u16(cd, p + 10), csize = u32(cd, p + 20) >>> 0, nlen = u16(cd, p + 28), xlen = u16(cd, p + 30), clen = u16(cd, p + 32), lho = u32(cd, p + 42) >>> 0;
      var name = new TextDecoder().decode(cd.subarray(p + 46, p + 46 + nlen));
      if (/\.csv$/i.test(name)) { found = {method: method, csize: csize, lho: lho, name: name}; break; }
      p += 46 + nlen + xlen + clen;
    }
    if (!found) throw new Error("No .csv file found inside the zip.");
    var lh = new Uint8Array(await file.slice(found.lho, found.lho + 30).arrayBuffer());
    var start = found.lho + 30 + u16(lh, 26) + u16(lh, 28);
    var raw = file.slice(start, start + found.csize).stream();
    if (found.method === 0) return raw;
    if (found.method !== 8) throw new Error("Unsupported zip compression method.");
    return raw.pipeThrough(new DecompressionStream("deflate-raw"));
  }
  async function cleanFiles(files, opts, progress) {
    var cleaners = [], total = {read: 0, kept: 0, masked: 0};
    for (var f = 0; f < files.length; f++) {
      var file = files[f], stream = /\.zip$/i.test(file.name) ? await zipEntryStream(file) : file.stream();
      var reader = stream.pipeThrough(new TextDecoderStream("utf-8", {fatal: false})).getReader();
      var cleaner = null, csv = null, buf = "", sniffed = false;
      for (;;) {
        var r = await reader.read();
        if (r.done) break;
        if (!sniffed) {
          buf += r.value;
          if (buf.indexOf("\n", buf.indexOf("\n") + 1) < 0 && buf.length < 4000) continue;
          cleaner = sniff(buf, opts);
          if (!cleaner) throw new Error(file.name + ": not a Petrinex volumetrics file or a BC Energy Regulator production file.");
          var c2 = cleaner; csv = new CsvReader(function (row) { c2.row(row); });
          csv.feed(buf); sniffed = true;
        } else csv.feed(r.value);
        if (progress) progress(f, files.length, cleaner ? cleaner.stats.read : 0);
      }
      if (!sniffed) { cleaner = sniff(buf, opts); if (!cleaner) throw new Error(file.name + ": empty or unrecognised file."); var c3 = cleaner; csv = new CsvReader(function (row) { c3.row(row); }); csv.feed(buf); }
      csv.end();
      cleaners.push(cleaner);
    }
    var kinds = {}; cleaners.forEach(function (c) { kinds[c.constructor.kind] = 1; });
    if (Object.keys(kinds).length > 1) throw new Error("Please clean Alberta/Saskatchewan files and BC files separately.");
    var res = cleaners.map(function (c) { return c.finish(); });
    var rows = [], header = res[0].header;
    res.forEach(function (x) { for (var i = 0; i < x.rows.length; i++) rows.push(x.rows[i]); total.read += x.stats.read; total.kept += x.stats.kept; total.masked += x.stats.masked; });
    if (cleaners[0] instanceof BcCleaner && cleaners.length > 1) { // merge duplicates across files like the Python groupby
      var agg = {}; rows.forEach(function (r) { var k = r[3] + "\t" + r[1] + "\t" + r[0]; var a = agg[k]; if (!a) agg[k] = r.slice(); else { a[4] += r[4]; if (r[5] !== null && (a[5] === null || r[5] > a[5])) a[5] = r[5]; } });
      rows = Object.keys(agg).map(function (k) { return agg[k]; }); total.kept = rows.length;
    }
    return {header: header, rows: rows, stats: total, kind: cleaners[0].constructor.kind};
  }

  var api = {CsvReader: CsvReader, VolCleaner: VolCleaner, BcCleaner: BcCleaner, toCsv: toCsv, sniff: sniff, cleanFiles: cleanFiles, splitLine: splitLine};
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.TWClean = api;
})(typeof window !== "undefined" ? window : this);
