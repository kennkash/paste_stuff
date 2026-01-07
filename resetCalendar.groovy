import com.onresolve.scriptrunner.runner.rest.common.CustomEndpointDelegate
import groovy.transform.BaseScript

import javax.ws.rs.core.MediaType
import javax.ws.rs.core.MultivaluedMap
import javax.ws.rs.core.Response

@BaseScript CustomEndpointDelegate delegate

/**
 * UI Fragment should call:
 *   /rest/scriptrunner/latest/custom/resetHolidayCalKickoff
 *
 * This endpoint:
 *  1) shows a flag immediately
 *  2) fires your existing long-running GET endpoint via AJAX
 *  3) optionally refreshes or navigates away (configurable)
 */
resetHolidayCalKickoff { MultivaluedMap queryParams ->

    // ✅ Your existing endpoint (the one that actually does the work)
    // If it’s on STG, keep it as absolute like your example.
    // If you want it to run on the same host the user is on, use AJS.contextPath() + relative URL in JS.
    String longRunnerEndpoint = "/rest/scriptrunner/latest/custom/resetHolidayCal"

    // Optional behavior after starting:
    // - "none"      => stay on this tiny page (not great UX)
    // - "back"      => go back to previous page
    // - "reload"    => reload current page (often best)
    String afterStart = "back"

    String afterStartJs = (afterStart == "reload") ?
        "window.location.reload(true);" :
        (afterStart == "back") ?
            "window.history.back();" :
            "/* no nav */"

    String html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Processing…</title>
  <meta name="decorator" content="atl.general"/>
</head>
<body>
<script>
(function (\$) {
  function kickoff() {
    // 1) Flag immediately
    if (window.AJS && AJS.flag) {
      AJS.flag({
        type: 'info',
        title: 'Request received',
        body: 'Your request is being processed. Please allow about 10 minutes for completion.',
        close: 'auto'
      });
    }

    // 2) Fire the real endpoint async (GET)
    // Prefer relative + contextPath so it works in any environment (stg/prod) without hardcoding host.
    var url = (window.AJS && AJS.contextPath)
      ? (AJS.contextPath() + '${longRunnerEndpoint}')
      : ('${longRunnerEndpoint}');

    if (window.AJS && AJS.\$) {
      AJS.\$.ajax({
        url: url,
        type: 'GET'
      });
    } else if (\$ && \$.ajax) {
      \$.ajax({ url: url, type: 'GET' });
    } else {
      // super basic fallback
      var img = new Image();
      img.src = url + (url.indexOf('?') >= 0 ? '&' : '?') + 't=' + Date.now();
    }

    // 3) Navigate away shortly so user isn’t left on a blank page
    setTimeout(function () {
      ${afterStartJs}
    }, 600);
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    kickoff();
  } else {
    document.addEventListener('DOMContentLoaded', kickoff);
  }
})(window.AJS ? AJS.\$ : window.jQuery);
</script>

<p>Starting…</p>
</body>
</html>
"""

    return Response.ok(html, MediaType.TEXT_HTML).build()
}