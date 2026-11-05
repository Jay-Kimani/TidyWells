(function () {
  var box = document.getElementById("subscribe"); if (!box) return;
  var action = window.TIDYWELLS_NEWSLETTER_ACTION || "";
  var rss = document.querySelector('link[rel=alternate][type="application/rss+xml"]').href;
  var html = '<div class="panel" style="margin:16px 0"><b>New analysis, about every two weeks</b>' +
    '<p style="margin:4px 0;font-size:14px;color:var(--muted)">No sales emails. ';
  if (action) {
    html += 'Get each post by email, or use <a href="' + rss + '">RSS</a>.</p>' +
      '<form action="' + action.replace(/"/g, "") + '" method="post" target="_blank" style="display:flex;gap:8px;flex-wrap:wrap">' +
      '<input type="hidden" value="1" name="embed"><input type="email" name="email" required placeholder="you@example.com" aria-label="Email address" style="flex:1;min-width:200px">' +
      '<button type="submit">Subscribe</button></form>' +
      '<p style="margin:6px 0 0;font-size:12px;color:var(--muted)">By subscribing you agree to receive an email when a new Tidywells post is published. Unsubscribe any time with the link in every email.</p>';
  } else {
    html += 'Follow by <a href="' + rss + '">RSS</a> (email signup coming soon).</p>';
  }
  html += '<p style="margin:8px 0 0;font-size:14px">Prefer your inbox? <a href="https://tidywells.substack.com/" target="_blank" rel="noopener"><b>Subscribe on Substack</b></a>.</p>';
  box.innerHTML = html + '</div>';
})();
