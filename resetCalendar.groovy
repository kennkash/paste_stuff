import com.atlassian.confluence.pages.Attachment
import com.atlassian.confluence.pages.Page
import static org.apache.commons.collections.CollectionUtils.*
import com.onresolve.scriptrunner.runner.rest.common.CustomEndpointDelegate
import groovy.transform.BaseScript
import javax.ws.rs.core.MediaType
import javax.ws.rs.core.MultivaluedMap
import javax.ws.rs.core.Response
 
@BaseScript CustomEndpointDelegate delegate
 
deleteGhostAttachments { MultivaluedMap queryParams ->
    def currentPageID = queryParams.getFirst("pageID") as Long

def dialog =
        """<section role="dialog" id="sr-dialog" class="aui-layer aui-dialog2 aui-dialog2-medium" aria-hidden="true" data-aui-remove-on-hide="true">
            <header class="aui-dialog2-header" style="background: #0052CC">
                <h2 class="aui-dialog2-header-main" style="color: #FFFFFF">Remove Ghost Attachments</h2>
            </header>
            <div class="aui-dialog2-content">
                <p>When you select 'Delete Ghost Attachments' You will have successfully initiated the removal of hidden attachments that exist in the database for this page but are not displayed on the page itself. These "ghost attachments" may clutter the database without serving any visible purpose on the page. <br><br> To learn more about this action and its implications, you can visit the designated information page linked below. Please note that this operation will exclusively target attachments that are not currently visible on the page, ensuring a streamlined and efficient cleanup process.</p><br><a href="https://confluence.samsungaustin.com/x/kD2vEg" target="_blank">More Details</a>
            </div>
            <footer class="aui-dialog2-footer">
                <div class="aui-dialog2-footer-actions">
                    <button id="dialog-submit-button" class="aui-button aui-button-primary">Delete Ghost Attachments</button>
                    <button id="dialog-close-button" class="aui-button aui-button-link" style="margin-left: 10px;">Close</button>
                </div>
                <div class="aui-dialog2-footer-hint">You only need to run this operation once per page</div>
            </footer>
            <script>
  (function (\$) {
    \$(function () {
        // Listen for when any AJS dialog2 is shown
        AJS.dialog2.on("show", function (e) {
            var targetId = e.target.id;
            // Check if the shown dialog is the one you're interested in
            if (targetId == "sr-dialog") { // Adjust the ID as necessary
                var someDialog = AJS.dialog2(e.target);
                
                // Set up a click event handler for the submit button
                \$(e.target).find("#dialog-submit-button").click(function (e) {
                    e.preventDefault(); // Prevent the default form submission

                    // Optionally, change the button text or disable it to indicate processing
                    \$(this).text('Processing...').prop('disabled', true);
                    
                    // Replace with your API endpoint and the appropriate currentPageID
                    var apiEndpoint = `https://confluencestg.samsungaustin.com/rest/scriptrunner/latest/custom/deleteGhostAttachments2?pageID=${currentPageID}`;
                    
                    \$.ajax({
                        url: apiEndpoint,
                        type: "GET", // Or "POST", depending on your endpoint
                        success: function(response) {
                            console.log("API call was successful:", response);
                            // Provide some immediate visual feedback that the API call was successful
                            AJS.flag({
                                type: 'success',
                                title: 'Operation Successful',
                                body: 'The page will refresh shortly.',
                                close: 'auto'
                            });

                            // Wait 4 seconds before refreshing the page
                            setTimeout(function() {
                                window.location.reload(true);
                            }, 4000);
                        },
                        error: function(xhr, status, error) {
                            console.error("API call failed:", error);
                            // Handle error, maybe display an error message
                            AJS.flag({
                                type: 'error',
                                title: 'Operation Failed',
                                body: 'Please try again later.',
                                close: 'auto'
                            });
                            // Re-enable the button if there's an error
                            \$(this).text('Try Again').prop('disabled', false);
                        }
                    });
                });

                // Set up a click event handler for the close button, if needed
                \$(e.target).find("#dialog-close-button").click(function (e) {
                    e.preventDefault(); // Prevent the default action
                    someDialog.hide();
                    someDialog.remove();
                });

                // Add any other setup or event handlers you need for this dialog
            }
        });
    });
})(AJS.\$);

            </script>
</section>
        
        """

    Response.ok().type(MediaType.TEXT_HTML).entity(dialog.toString()).build()

}
