(function () {
  function updateTotal(totalVisible) {
    var total = document.querySelector(".compact-count span");

    if (total) {
      total.textContent = totalVisible;
    }
  }

  function removeEmptySection(article) {
    var remainingStickers = article.querySelectorAll(".compact-stickers form").length;
    var sectionCount = article.querySelector("header span");

    if (sectionCount) {
      sectionCount.textContent = remainingStickers;
    }

    if (remainingStickers === 0) {
      article.remove();
    }
  }

  function showEmptyState(data) {
    var list = document.querySelector(".compact-list");

    if (!list || list.querySelector(".compact-section")) {
      return;
    }

    var emptyState = document.createElement("section");
    emptyState.className = "empty-state";
    emptyState.innerHTML = "<h2></h2><p>Revise a busca ou alterne entre pendentes e adquiridas.</p>";
    emptyState.querySelector("h2").textContent = data.emptyTitle;
    list.replaceWith(emptyState);
  }

  function redirectToLogin(response) {
    return response.json()
      .catch(function () {
        return {};
      })
      .then(function (data) {
        window.location.assign(data.loginUrl || "/login");
        throw new Error("session-expired");
      });
  }

  document.addEventListener("submit", function (event) {
    var form = event.target;

    if (!form.closest(".compact-stickers")) {
      return;
    }

    event.preventDefault();

    var button = form.querySelector(".compact-sticker");
    if (button && button.disabled) {
      return;
    }
    if (button) {
      button.disabled = true;
    }

    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      },
      credentials: "same-origin"
    })
      .then(function (response) {
        if (response.status === 401) {
          return redirectToLogin(response);
        }
        if (!response.ok) {
          throw new Error("Nao foi possivel atualizar a figurinha.");
        }
        return response.json();
      })
      .then(function (data) {
        var article = form.closest(".compact-section");

        form.remove();
        if (article) {
          removeEmptySection(article);
        }
        updateTotal(data.compactList.totalVisible);
        showEmptyState(data.compactList);
      })
      .catch(function (error) {
        if (error && error.message === "session-expired") {
          return;
        }
        form.submit();
      })
      .finally(function () {
        if (button) {
          button.disabled = false;
        }
      });
  });
})();
