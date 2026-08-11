/* Mobile-only blocker: auto-allow when the live viewport actually has enough
   room for the desktop layout (>= 1024px). Fires only after the server already
   gated this visit, so JS-off visitors simply stay on the notice page. */
(function () {
    'use strict';

    var MIN_WIDTH = 1024;
    var noticeEl = document.getElementById('mobile-notice');
    var nextPath = noticeEl ? noticeEl.getAttribute('data-next') || '/' : '/';

    function enoughSpace() {
        var w = window.innerWidth || window.outerWidth || 0;
        return w >= MIN_WIDTH;
    }

    function allowAndProceed() {
        if (window.__velareNoticeAllowed) return;
        window.__velareNoticeAllowed = true;

        var payload = {
            method: 'POST',
            credentials: 'same-origin'
        };

        window.fetch('/mobile-notice/allow', payload)
            .catch(function () {})
            .then(function () {
                window.location.replace(nextPath);
            });
    }

    if (enoughSpace()) {
        allowAndProceed();
    } else {
        window.addEventListener('resize', function () {
            if (enoughSpace()) allowAndProceed();
        });
    }
})();
