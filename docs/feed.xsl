<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" encoding="UTF-8"/>
<xsl:template match="/rss/channel"><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>Tidywells feed</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:720px;margin:0 auto;padding:24px 16px;background:#0a0f16;color:#e6e9ec}a{color:#6aa6f0}.box{border:1px solid #2a323b;border-radius:8px;padding:12px 14px;margin:16px 0;background:#171d24}code{background:#0a0f16;padding:2px 6px;border-radius:4px}small{color:#8a96a3}</style></head>
<body><h1>Tidywells feed</h1>
<div class="box">This is an RSS feed. Copy this address into a feed reader such as Feedly or NetNewsWire: <code>https://jay-kimani.github.io/TidyWells/feed.xml</code><br/><a href="https://jay-kimani.github.io/TidyWells/">Back to the site</a></div>
<xsl:for-each select="item"><div class="box"><b><a href="{link}"><xsl:value-of select="title"/></a></b><br/><small><xsl:value-of select="pubDate"/></small><p><xsl:value-of select="description"/></p></div></xsl:for-each>
</body></html></xsl:template></xsl:stylesheet>
