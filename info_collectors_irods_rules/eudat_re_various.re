# The following code handles log messages from EUDAT B2SAFE rules
# Received from Claudio Cacciari

# This code is to be copied into:
# opt/eudat/b2safe/rulebase/

Modified version of the function EUDATMessage:

# It manages the writing and reading of log messages to/from external log services.
# The current implementation writes the logs to specific log file.
#
# Return
#  no response is expected
#
# Parameters:
#   *queue     [IN]    the queue which will host the message
#   *message   [IN]    the message to be sent
#
# Author: Claudio Cacciari, Cineca
#-------------------------------------------------------------------------------
EUDATMessage(*queue, *message) {

    logInfo("[EUDATMessage] pushing the message to topic *queue");
    getMessageParameters(*msgConfPath, *enabled);
    if (*enabled && $userNameClient != "anonymous") {
        logInfo("[EUDATMessage] sending message '*message' to the topic '*queue'");
        msiExecCmd("rabbitclient.py", "*queue '*message'",
                   "null", "null", "null", *outMessage);
        msiGetStderrInExecCmdOut(*outMessage, *output);
    }
}
