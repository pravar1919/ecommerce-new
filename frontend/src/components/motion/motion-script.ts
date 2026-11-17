/**
 * Runs in <head> before first paint. Marks the document as motion-capable only when JS runs and
 * the user hasn't asked for reduced motion, so CSS can pre-hide below-the-fold reveals. Without JS
 * (or for crawlers) nothing is ever hidden. A CSS failsafe reveals everything after 4s regardless.
 */
export const MOTION_BOOTSTRAP = `(function(){try{var d=document.documentElement;var m=window.matchMedia("(prefers-reduced-motion: reduce)");d.dataset.motion=m.matches?"reduce":"ok";m.addEventListener&&m.addEventListener("change",function(e){d.dataset.motion=e.matches?"reduce":"ok"})}catch(e){}})();`;
