import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

import com.atlassian.sal.api.component.ComponentLocator
import com.atlassian.sal.api.executor.ThreadLocalDelegateExecutorFactory
import com.onresolve.scriptrunner.runner.rest.common.CustomEndpointDelegate
import groovy.transform.BaseScript

import javax.ws.rs.core.MultivaluedMap
import javax.ws.rs.core.MediaType
import javax.ws.rs.core.Response

@BaseScript CustomEndpointDelegate delegate

resetHolidayCal { MultivaluedMap queryParams ->

    String confluenceURL = "https://confluencestg.samsungaustin.com/rest/confiforms/1.0/updateFieldValue/51860671/coverage?query=!id:%5Bempty%5D&fv="

    String[] suffixes = [
        "date1:", "date2:", "date3:", "date4:", "date5:", "date6:", "date7:", "date8:",
        "date9:", "date10:", "date11:", "date12:", "date13:", "date14:", "date15:", "date16:",
        "mainpoc:", "ops:", "opsdate1:", "opsdate2:", "opsdate3:", "opsdate4:", "opsdate5:",
        "opsdate6:", "opsdate7:", "opsdate8:", "opsdate9:", "opsdate10:", "opsdate11:",
        "opsdate12:", "opsdate13:", "opsdate14:", "opsdate15:", "opsdate16:"
    ]

    List<String> urls = suffixes.collect { suffix -> confluenceURL + suffix }

    // Return immediately, run the long work async.
    def threadLocalFactory = ComponentLocator.getComponent(ThreadLocalDelegateExecutorFactory)
    def executor = threadLocalFactory.createExecutorService(Executors.newSingleThreadExecutor())

    executor.submit({
        boolean allSuccessful = true

        def makePutRequest = { String urlString ->
            try {
                String bearerToken = "faketoken"
                HttpURLConnection connection = (HttpURLConnection) new URL(urlString).openConnection()
                connection.setRequestMethod("PUT")
                connection.setRequestProperty("Content-Type", "application/json")
                connection.setRequestProperty("Accept", "application/json")
                connection.setRequestProperty("Authorization", "Bearer " + bearerToken)
                connection.setDoOutput(true)

                int code = connection.getResponseCode()
                if (code == HttpURLConnection.HTTP_OK) {
                    log.warn("Successfully updated: ${urlString}")
                    return true
                } else {
                    log.warn("Failed to update: ${urlString}. Response code: ${code}")
                    return false
                }
            } catch (Exception e) {
                log.warn("Error during PUT request (${urlString}): ${e.message}", e)
                return false
            }
        }

        urls.each { u ->
            if (!makePutRequest(u)) {
                allSuccessful = false
            }
        }

        // At this point you *cannot* reliably show a UI flag (the user isn't “waiting” on the request anymore).
        // Best options: log + email the user + write a status somewhere.
        log.warn("resetHolidayCal COMPLETE. allSuccessful=${allSuccessful}")

    } as Runnable)

    // Immediate feedback to the user
    String flagJs = """
      <script>
        AJS.flag({
          type: 'info',
          title: 'Request received',
          body: 'Your request is being processed. Please allow ~10 minutes for completion.',
          close: 'auto'
        });
      </script>
    """

    return Response.ok(flagJs, MediaType.TEXT_HTML).build()
}