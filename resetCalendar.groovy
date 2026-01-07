import java.net.HttpURLConnection;
import java.net.URL;
import com.onresolve.scriptrunner.runner.rest.common.CustomEndpointDelegate
import groovy.transform.BaseScript
import javax.ws.rs.core.MultivaluedMap
import javax.ws.rs.core.MediaType
import javax.ws.rs.core.Response
// MAKE SURE TO REMOVE THE VALIDATOR RULE FROM THE PEOPLE FORM ON THE HOLIDAY COVERAGE MASTERFORM PAGE HERE 
// https://confluence.samsungaustin.com/display/HOLIDAY/Holiday+Coverage+Master+Form
// Script takes about 5-10 minutes to complete

@BaseScript CustomEndpointDelegate delegate

resetHolidayCal { MultivaluedMap queryParams ->
    // Base URL for the Confluence API
    String confluenceURL = "https://confluencestg.samsungaustin.com/rest/confiforms/1.0/updateFieldValue/51860671/coverage?query=!id:%5Bempty%5D&fv=";

    // List of suffixes for the URLs
    String[] suffixes = ["date1:", "date2:", "date3:", "date4:", "date5:", "date6:", "date7:", "date8:", "date9:", "date10:", 
                        "date11:", "date12:", "date13:", "date14:", "date15:", "date16:", "mainpoc:", "ops:", "opsdate1", "opsdate2",
                        "opsdate3:", "opsdate4:", "opsdate5:", "opsdate6:", "opsdate7:", "opsdate8:", "opsdate9:", "opsdate10:",
                        "opsdate11:", "opsdate12:", "opsdate13:", "opsdate14:", "opsdate15:","opsdate16:"];

    // Create the full URLs by appending each suffix to the base URL
    List<String> urls = suffixes.collect { suffix -> confluenceURL + suffix }

    // Function to make a PUT request
    def makePutRequest= { String urlString ->
        try {
            // Enter your Bearer token here
            String bearerToken = "faketoken";
            URL url = new URL(urlString);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("PUT");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Authorization", "Bearer " + bearerToken);
            connection.setDoOutput(true);

            // Check the response
            if (connection.getResponseCode() == HttpURLConnection.HTTP_OK) {
                log.warn("Successfully updated: " + urlString);
                return true
            } else {
                log.warn("Failed to update: " + urlString + ". Response code: " + connection.getResponseCode());
                return false
            }
        } catch (Exception e) {
            log.warn("Error during PUT request: " + e.getMessage());
            return false
        }
    }


    boolean allSuccessful = true

    // Run the PUT requests
    urls.each { u ->
        boolean ok = makePutRequest(u)
        if (!ok) {
        // as soon as one request fails we mark the whole batch as failed
        allSuccessful = false
        }
    }

     String flagJs = allSuccessful ?
        """
        <script>
            AJS.flag({
                type: 'success',
                title: 'Operation Underway',
                body: 'Please wait 10 minutes for completion.',
                close: 'auto'
            });
        </script>
        """ :
        """
        <script>
            AJS.flag({
                type: 'error',
                title: 'Operation Failed',
                body: 'Please try again or contact your admins.',
                close: 'auto'
            });
        </script>
        """

    Response.ok(flagJs, MediaType.TEXT_HTML).build()
 }
