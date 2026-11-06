// Newsletter signup. Leave empty until you have an email service account.
// Paste the form action URL from your service's embed code (for example Buttondown's
// "embed-subscribe" URL). While empty, the page shows RSS only.
window.TIDYWELLS_NEWSLETTER_ACTION = "https://buttondown.com/api/emails/embed-subscribe/TidyWells";


// Comments (giscus). Enable Discussions on the repo, install the giscus app, then paste categoryId from https://giscus.app
window.TIDYWELLS_GISCUS={repo:"Jay-Kimani/TidyWells",repoId:"R_kgDOViBLug",category:"Comments",categoryId:"DIC_kwDOViBLus4DKW_A"};

// Comments without sign-in: your Cloudflare Worker URL and Turnstile site key (see workers/comments/README.md).
window.TIDYWELLS_COMMENTS_API="https://tidywells-comments.jonathandupuis747.workers.dev";
window.TIDYWELLS_TURNSTILE_SITEKEY="0x4AAAAAAFzv-FY4UZhVEvor";

// Cookieless analytics: Cloudflare dashboard > Analytics & Logs > Web Analytics > Add site (tidywells.com) > copy the token.
window.TIDYWELLS_CF_ANALYTICS_TOKEN = "b2b321b43f0a4327b1b0f58bdcc9953c";
// One labelled sponsor strip shown at the top of every page. Leave name empty to hide. URL must be https.
window.TIDYWELLS_SPONSOR={name:"",url:"",text:""};

// Shop: paste your storefront URL (https only) to switch on "View in store" buttons on shop.html. Optional per-product links:
// window.TIDYWELLS_SHOP_LINKS = {"poster-ab-oil": "https://..."} (keys are the data-slug values on shop.html).
window.TIDYWELLS_SHOP_URL = "";
