(function () {
  var dashboardScrollKey = "dashboard-scroll";
  var touchStartX = 0;
  var touchStartY = 0;
  var touchStartTime = 0;

  function previousPageIsDashboard() {
    var referrerUrl;

    if (!document.referrer) {
      return false;
    }

    try {
      referrerUrl = new URL(document.referrer);
    } catch (error) {
      return false;
    }

    return referrerUrl.origin === window.location.origin && referrerUrl.pathname === "/painel";
  }

  function shouldUseHistoryBack() {
    return (
      window.history.length > 1 &&
      previousPageIsDashboard() &&
      window.sessionStorage.getItem(dashboardScrollKey) !== null
    );
  }

  function goBackToPanel(fallbackUrl) {
    if (shouldUseHistoryBack()) {
      window.history.back();
      return;
    }

    window.location.href = fallbackUrl;
  }

  document.addEventListener("click", function (event) {
    var backLink = event.target.closest("[data-panel-back]");

    if (!backLink) {
      return;
    }

    event.preventDefault();
    goBackToPanel(backLink.href);
  });

  document.addEventListener("touchstart", function (event) {
    if (event.touches.length !== 1 || window.innerWidth > 820) {
      return;
    }

    var touch = event.touches[0];
    touchStartX = touch.clientX;
    touchStartY = touch.clientY;
    touchStartTime = Date.now();
  }, { passive: true });

  document.addEventListener("touchend", function (event) {
    if (!touchStartTime || window.innerWidth > 820 || event.changedTouches.length !== 1) {
      return;
    }

    var touch = event.changedTouches[0];
    var deltaX = touch.clientX - touchStartX;
    var deltaY = Math.abs(touch.clientY - touchStartY);
    var elapsed = Date.now() - touchStartTime;

    touchStartTime = 0;

    if (touchStartX > 44 || deltaX < 86 || deltaY > 60 || elapsed > 700) {
      return;
    }

    var backLink = document.querySelector("[data-panel-back]");

    if (backLink) {
      goBackToPanel(backLink.href);
    }
  }, { passive: true });
})();
