(function () {
  var scrollKey = "dashboard-scroll";

  if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
  }

  function saveScrollPosition() {
    window.sessionStorage.setItem(scrollKey, String(window.scrollY || 0));
  }

  function restoreScrollPosition() {
    var savedPosition = window.sessionStorage.getItem(scrollKey);

    if (savedPosition === null) {
      return;
    }

    window.scrollTo({
      top: Number(savedPosition) || 0,
      left: 0,
      behavior: "auto"
    });
  }

  function replaceDashboardSection(documentFragment, selector) {
    var currentElement = document.querySelector(selector);
    var freshElement = documentFragment.querySelector(selector);

    if (currentElement && freshElement) {
      currentElement.replaceWith(freshElement);
    }
  }

  function refreshDashboardData() {
    var currentScroll = window.scrollY || 0;

    fetch(window.location.href, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      },
      cache: "no-store",
      credentials: "same-origin"
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Nao foi possivel atualizar o painel.");
        }
        return response.text();
      })
      .then(function (html) {
        var freshDocument = new DOMParser().parseFromString(html, "text/html");

        replaceDashboardSection(freshDocument, ".dashboard-hero");
        replaceDashboardSection(freshDocument, ".group-grid");
        window.scrollTo({
          top: currentScroll,
          left: 0,
          behavior: "auto"
        });
      })
      .catch(function () {
        return;
      });
  }

  document.addEventListener("click", function (event) {
    if (!event.target.closest("[data-dashboard-leave]")) {
      return;
    }

    saveScrollPosition();
  });

  window.addEventListener("pagehide", saveScrollPosition);
  window.addEventListener("pageshow", function () {
    restoreScrollPosition();
    refreshDashboardData();
  });
})();
