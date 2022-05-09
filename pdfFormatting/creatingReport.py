import pdfkit
import os
import webbrowser
# These html files contains the structure of report page and also contains the path of graphs which we have created.
# Then these html files will be further converted into pdf using pdfkit package.

try:

    pdfkit.from_file([ 
                      './pdfFormatting/public/index.html',
                      './pdfFormatting/public/reposComparison.html',
                      './pdfFormatting/public/ownersComparison.html',
                      './pdfFormatting/public/prsComparison.html',
                      './pdfFormatting/public/abandonedComparison.html',
                      './pdfFormatting/public/locComparison.html',
                      './pdfFormatting/public/openersComparison.html',
                      './pdfFormatting/public/overviewOpenCount.html',
                      './pdfFormatting/public/rvwThrdComparison.html',
                      './pdfFormatting/public/rvwResolvedComparison.html',
                      './pdfFormatting/public/rvwCommentsComparison.html',
                      './pdfFormatting/public/reviewersComparison.html',
                      './pdfFormatting/public/overviewReviewsCount.html',
                      './pdfFormatting/public/approversComparison.html',
                      './pdfFormatting/public/overviewApprovesCount.html',
                      './pdfFormatting/public/inspectionRateTime.html',
                      './pdfFormatting/public/preIntegrationTime.html',
                      './pdfFormatting/public/integrationTime.html',
                      './pdfFormatting/public/overviewIntegrationTime.html',
                      './pdfFormatting/public/top30NamesForPR.html',
                      './pdfFormatting/public/top30NamesForLOC.html',
                      './pdfFormatting/public/prNamingGuidance.html'
                    ], "report.pdf",
                    options = {
                            'enable-local-file-access': None,
                        }
                    )
except Exception as e:
    print(e)