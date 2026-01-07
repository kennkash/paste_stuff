import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

import com.onresolve.scriptrunner.runner.rest.common.CustomEndpointDelegate
import groovy.transform.BaseScript

import javax.ws.rs.core.MultivaluedMap
import javax.ws.rs.core.MediaType
import javax.ws.rs.core.Response

@BaseScript CustomEndpointDelegate delegate

resetHolidayCal { MultivaluedMap queryParams ->

    String confluenceURL =
        "https://confluencestg.samsungaustin.com/rest/confiforms/1.0/updateFieldValue/51860671/coverage?query=!id:%5Bempty%5D&fv="

    String[] suffixes = [
        "date1:", "date2:", "date3:", "date4:", "date5:", "date6:", "date7:", "date8:",
        "date9:", "date10:", "date11:", "date12:", "date13:", "date14:", "date15:", "date16:",
        "mainpoc:", "ops:", "opsdate1:", "opsdate2:", "opsdate3:", "opsdate4:", "opsdate5:",
        "opsdate6:", "opsdate7:", "opsdate8:", "opsdate9:", "opsdate10:", "opsdate11:",
        "opsdate12:", "opsdate13:", "opsdate14:", "opsdate15:", "opsdate16:"
    ]

    List<String> urls = suffixes.collect { confluenceURL + it }

    // 🔹 Fire-and-forget executor
    def executor = Executors.newSingleThreadExecutor()

    executor.submit({
        boolean allSuccessful = true

        def makePutRequest = { String urlString ->
            try {
                HttpURLConnection conn =
                    (HttpURLConnection) new URL(urlString).openConnection()
                conn.setRequestMethod("PUT")
                conn.setRequestProperty("Content-Type", "application/json")
                conn.setRequestProperty("Accept", "application/json")
                conn.setRequestProperty("Authorization", "Bearer faketoken")
                conn.setDoOutput(true)

                int code = conn.getResponseCode()
                if (code == 200) {
                    log.warn("Updated: ${urlString}")
                    return true
                } else {
                    log.warn("FAILED ${urlString} → ${code}")
                    return false
                }
            } catch (Exception e) {
                log.warn("ERROR ${urlString}", e)
                return false
            }
        }

        urls.each { u ->
            if (!makePutRequest(u)) {
                allSuccessful = false
            }
        }

        log.warn("resetHolidayCal finished. success=${allSuccessful}")

        executor.shutdown()
    } as Runnable)

    // 🔹 Immediate user feedback
    String flagJs = """
    <script>
      AJS.flag({
        type: 'info',
        title: 'Request received',
        body: 'Your request is being processed. Please allow about 10 minutes for completion.',
        close: 'auto'
      });
    </script>
    """

    Response.ok(flagJs, MediaType.TEXT_HTML).build()
}