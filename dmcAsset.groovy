I have this script in scriptrunner for a custom macro for confluence data center: 
import groovyx.net.http.RESTClient
import groovyx.net.http.HttpResponseException
import org.json.JSONObject
import org.json.JSONArray

def restClient = new RESTClient("https://jira.samsungaustin.com")

def headers = [
    "Authorization": "Bearer ABCDEFGHIJKLMNOP"
]

def addonsData
def htmlTable = ""

try {
    def response = restClient.get(
        path: "/rest/insight/1.0/iql/objects",
        query: [
            objectSchemaId: "5",          // SOP schema
            resultPerPage: "600",
            iql          : parameters.IQL
        ],
        headers: headers
    )

     log.warn("Response Status: ${response.status}")

    if (response.status == 200) {
        addonsData = new JSONObject(response.data)
        log.warn("Parsed Response: ${addonsData.toString(2)}")
    } else {
        log.warn("Failed to fetch data. HTTP Status: ${response.status}")
        addonsData = new JSONObject("{}")
    }
} catch (HttpResponseException ex) {
    log.warn("HTTP Request failed: ${ex.message}")
    addonsData = new JSONObject("{}")
} catch (Exception e) {
    log.warn("Unexpected error: ${e.message}")
    addonsData = new JSONObject("{}")
}

/* -------------------------------------------------------------------------
   Build HTML table – only if we got a proper JSON payload with objectEntries
   ------------------------------------------------------------------------- */
if (addonsData && addonsData.length() > 0) {
    def objectEntries = addonsData.optJSONArray("objectEntries")
    if (objectEntries && objectEntries.length() > 0) {

        /* ---------- table header (added Employee ID) ---------- */
        htmlTable += """
<table class='aui rlabs-ifc-insight-objects-macro-view-table full-width'>
    <thead style='background-color:#f2f2f2; position:sticky; top:40px; z-index:1'>
        <tr>
            <th>Site</th>
            <th>SOP ID</th>
            <th>SOP Published Page</th>
            <th>SOP Type</th>
            <th>SOP Subtype</th>
            <th>Document Owner</th>
            <th>Team Name</th>
            <th>Target Audience</th>
            <th>Revision Date</th>
            <th>Expiration Date</th>
            <th>Certification</th>
            <th>Specification ID</th>
            <th>Status</th>
            <th>SharePoint ID</th>
        </tr>
    </thead>
    <tbody>
"""

        /* ---------- iterate over each Insight object ---------- */
        objectEntries.each { entry ->

            // ---- default placeholders ----
            def site               = "N/A"
            def sopID              = "N/A"
            def sopPublishedPageTitle = "N/A"
            def sopPublishedPageUrl   = "N/A"
            def sopType            = "N/A"
            def sopSubType         = "N/A"
            def documentOwner      = "N/A"
            def teamName           = ""
            def targetAudience     = ""
            def revisionDate       = "N/A"
            def expirationDate     = "N/A"
            def certification      = ""
            def sopSourceID        = "N/A"
            def specificationId    = ""
            def status             = "N/A"

            // When we encounter Document Owner we also store the referenced object id
            Integer ownerObjectId = null

            def attributes = entry.optJSONArray("attributes")
            attributes?.each { attribute ->

                switch (attribute.optInt("objectTypeAttributeId")) {

                    // -------------------------------------------------------------
                    // Existing cases – unchanged (only trimmed for brevity)
                    // -------------------------------------------------------------
                    case 1112: // Site
                        site = attribute.optJSONArray("objectAttributeValues")
                               ?.optJSONObject(0)
                               ?.optString("displayValue", "N/A")
                        break

                    case 1128: // SOP ID
                        sopID = attribute.optJSONArray("objectAttributeValues")
                               ?.optJSONObject(0)
                               ?.optString("displayValue", "N/A")
                        break

                    case 1144: // SOP Published Page (Confluence)
                        def confluencePage = attribute.optJSONArray("objectAttributeValues")
                                            ?.optJSONObject(0)
                                            ?.optJSONObject("confluencePage")
                        if (confluencePage) {
                            sopPublishedPageTitle = confluencePage.optString("title", "N/A")
                            sopPublishedPageUrl   = confluencePage.optString("url", "N/A")
                        }
                        break

                    case 1114: // SOP Type
                        sopType = attribute.optJSONArray("objectAttributeValues")
                                 ?.optJSONObject(0)
                                 ?.optString("displayValue", "N/A")
                        break

                    case 1115: // SOP Subtype
                        sopSubType = attribute.optJSONArray("objectAttributeValues")
                                    ?.optJSONObject(0)
                                    ?.optString("displayValue", "N/A")
                        break

                    // -------------------------------------------------------------
                    // NEW – Document Owner handling (capture reference id)
                    // -------------------------------------------------------------
                    case 1146: // Document Owner (reference to Employees schema)
            def ownerAttr = attribute?.objectAttributeValues?.getAt(0)

            // Name to display
            documentOwner = ownerAttr?.displayValue ?: "N/A"

            // Real Insight object id (ownerEmployeeId)
            ownerObjectId = ownerAttr?.referencedObject?.id
            if (ownerObjectId == null) {
                ownerObjectId = ownerAttr?.referencedObject?.objectId
            }
            break

                    case 1116: // Team Name (multi‑value)
                        def teamNameValues = attribute.optJSONArray("objectAttributeValues")
                        teamNameValues?.each { v ->
                            teamName += v.optString("displayValue", "") + "<br>"
                        }
                        if (teamName.endsWith("<br>")) teamName = teamName[0..-5]
                        break

                    case 1124: // Target Audience (multi‑value)
                        def targetAudienceValues = attribute.optJSONArray("objectAttributeValues")
                        targetAudienceValues?.each { v ->
                            targetAudience += v.optString("displayValue", "") + "<br>"
                        }
                        if (targetAudience.endsWith("<br>")) targetAudience = targetAudience[0..-5]
                        break

                    case 1117: // Revision Date
                        revisionDate = attribute.optJSONArray("objectAttributeValues")
                                     ?.optJSONObject(0)
                                     ?.optString("displayValue", "N/A")
                        break

                    case 1119: // Expiration Date
                        expirationDate = attribute.optJSONArray("objectAttributeValues")
                                         ?.optJSONObject(0)
                                         ?.optString("displayValue", "N/A")
                        break

                    case 1122: // Certification (multi‑value)
                        def certVals = attribute.optJSONArray("objectAttributeValues")
                        certVals?.each { cv ->
                            certification += cv.optString("displayValue", "") + "<br>"
                        }
                        if (certification.endsWith("<br>")) certification = certification[0..-5]
                        break

                    case 1391: // S2 SOP Source
                        sopSourceID = attribute.optJSONArray("objectAttributeValues")
                              ?.optJSONObject(0)
                              ?.optString("displayValue", "N/A")
                        break

                    case 1121: // Specification ID (multi‑value, split on space)
                        def specVals = attribute.optJSONArray("objectAttributeValues")
                        specVals?.each { sv ->
                            def full = sv.optString("displayValue", "")
                            specificationId += (full.contains(" ") ? full.split(" ")[0] : full) + "<br>"
                        }
                        if (specificationId.endsWith("<br>")) specificationId = specificationId[0..-5]
                        break

                    case 1120: // Status
                        status = attribute.optJSONArray("objectAttributeValues")
                                 ?.optJSONObject(0)
                                 ?.optString("displayValue", "N/A")
                        break
                } // switch
            } // each attribute
            

            /* -------------------- row output -------------------- */
            htmlTable += """
        <tr>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${site}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${sopID}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>
                <a href='${sopPublishedPageUrl}' target='_blank' style='color:#0073e6; text-decoration:none;'>
                    ${sopPublishedPageTitle}
                </a>
            </td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${sopType}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${sopSubType}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${documentOwner}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${teamName}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${targetAudience}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${revisionDate}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${expirationDate}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${certification}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${specificationId}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${status}</td>
            <td style='padding:8px; border-bottom:1px solid #ddd;'>${sopSourceID}</td>
        </tr>
"""
        } // each entry

        // close table
        htmlTable += """
    </tbody>
</table>
"""

    } else {
        log.warn("No object entries found in the response.")
    }
} else {
    log.warn("The response JSON is empty or invalid.")
}

// ---------------------------------------------------------------------
// Return the generated HTML (or log it for debugging)
// ---------------------------------------------------------------------
// log.warn("Generated HTML Table:\n${htmlTable}")
return htmlTable



When I enter this IQL: "Department"."Published Space Key" = IQADMCP AND "Certification" IS NOT EMPTY I get this error: 
Error rendering macro 'assets-macro'

begin -1, end 1, length 4

But when I use a different IQL like this for example: "Department"."Published Space Key" = s2DMCP AND "Certification" IS NOT EMPTY

I don't get the error... why is this? \
