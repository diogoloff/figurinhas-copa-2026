(function () {
  function updateSelectionProgress(selection) {
    var totalNumber = document.querySelector(".sticker-total .total-number");
    var totalLabel = document.querySelector(".sticker-total .total-label");
    var progressBar = document.querySelector(".sticker-total .progress-track span");
    var pendingCount = document.querySelector(".sticker-toolbar strong");

    if (totalNumber) {
      totalNumber.textContent = selection.completed + "/" + selection.total;
    }
    if (totalLabel) {
      totalLabel.textContent = selection.percent + "% completo";
    }
    if (progressBar) {
      progressBar.style.width = selection.percent + "%";
    }
    if (pendingCount) {
      pendingCount.textContent = selection.pending + " pendentes";
    }
  }

  function updateStickerTile(form, sticker, selection) {
    var button = form.querySelector(".sticker-tile");
    var state = form.querySelector(".sticker-state");

    if (!button) {
      return;
    }

    button.classList.toggle("is-collected", sticker.collected);
    button.setAttribute("aria-pressed", sticker.collected ? "true" : "false");
    if (state) {
      state.textContent = sticker.state;
    }

    if (selection.pendingOnly && sticker.collected) {
      form.remove();
    }
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

    if (!form.closest(".sticker-mark-grid")) {
      return;
    }

    event.preventDefault();

    var button = form.querySelector(".sticker-tile");
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
        updateStickerTile(form, data.sticker, data.selection);
        updateSelectionProgress(data.selection);
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
