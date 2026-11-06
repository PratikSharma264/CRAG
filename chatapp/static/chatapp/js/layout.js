/**
 * Collapsible sidebar and knowledge-base panel.
 * Loaded in <head> (not deferred) so the saved state is applied before first paint.
 */
(function () {
  "use strict";

  var root = document.documentElement;
  var PARTS = ["sidebar", "kb"];
  var STORAGE = { sidebar: "clinicalrag-sidebar", kb: "clinicalrag-kb" };
  var LABELS = {
    sidebar: { expanded: "Collapse sidebar", collapsed: "Expand sidebar" },
    kb: { expanded: "Hide knowledge base", collapsed: "Show knowledge base" }
  };

  function read(key) {
    try { return localStorage.getItem(key); } catch (error) { return null; }
  }

  function write(key, value) {
    try { localStorage.setItem(key, value); } catch (error) { /* state just won't persist */ }
  }

  function isCollapsed(part) {
    return root.getAttribute("data-" + part) === "collapsed";
  }

  function syncButtons(part) {
    var collapsed = isCollapsed(part);
    var label = LABELS[part][collapsed ? "collapsed" : "expanded"];
    document.querySelectorAll("[data-" + part + "-collapse]").forEach(function (button) {
      button.setAttribute("aria-expanded", String(!collapsed));
      button.setAttribute("aria-label", label);
      button.setAttribute("title", label);
    });
  }

  function setCollapsed(part, collapsed) {
    if (collapsed) root.setAttribute("data-" + part, "collapsed");
    else root.removeAttribute("data-" + part);
    write(STORAGE[part], collapsed ? "collapsed" : "expanded");
    syncButtons(part);
  }

  // Apply saved state immediately, before the page is drawn.
  PARTS.forEach(function (part) {
    if (read(STORAGE[part]) === "collapsed") root.setAttribute("data-" + part, "collapsed");
  });

  document.addEventListener("DOMContentLoaded", function () {
    PARTS.forEach(function (part) {
      syncButtons(part);
      document.querySelectorAll("[data-" + part + "-collapse]").forEach(function (button) {
        button.addEventListener("click", function () {
          setCollapsed(part, !isCollapsed(part));
        });
      });
    });
  });
})();
