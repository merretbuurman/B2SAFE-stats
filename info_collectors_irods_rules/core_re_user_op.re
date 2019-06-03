# The following 5 rules all send accounting info of type "operation"
# Received from Claudio Cacciari

# This code is to be copied into:
# /etc/irods/core.re

# it triggers collection creation and registration (imkdir, ireg, irsync collections)
acPostProcForCollCreate() {
  *op_info = "trigger=acPostProcForCollCreate, collName=$collName,"
          ++ " collParentName=$collParentName, connectOption=$connectOption,"
          ++ " rodsZoneClient=$rodsZoneClient, rodsZoneProxy=$rodsZoneProxy,"
          ++ " userNameClient=$userNameClient, clientAddr=$clientAddr"

  writeLine( "serverLog", "DEBUG: *op_info");
  if ($userNameClient != "anonymous") {
    msiExecCmd("rabbitclient.py", "seadatacloud user_op '*op_info'",
               "null", "null", "null", *outMessage);
    msiGetStderrInExecCmdOut(*outMessage, *output);
  }
}

# it triggers iput, imv, icp, irsync objects, irepl, ichksum
acPostProcForModifyDataObjMeta() {
  *op_info = "trigger=acPostProcForModifyDataObjMeta, chksum=$chksum,"
          ++ " connectOption=$connectOption, dataId=$dataId,"
          ++ " dataSize=$dataSize, dataType=$dataType, destRescName=$destRescName,"
          ++ " filePath=$filePath, objPath=$objPath, replNum=$replNum, replStatus=$replStatus,"
          ++ " rescName=$rescName, rodsZoneClient=$rodsZoneClient, rodsZoneProxy=$rodsZoneProxy,"
          ++ " userNameClient=$userNameClient, userNameProxy=$userNameProxy, writeFlag=$writeFlag,"
          ++ " clientAddr=$clientAddr"
 
  if ($userNameClient != "anonymous") {
    msiExecCmd("rabbitclient.py", "seadatacloud user_op '*op_info'",
               "null", "null", "null", *outMessage);
    msiGetStderrInExecCmdOut(*outMessage, *output);
  }
}

# it triggers iput -f, irsync, iget, igetwild, icp
acPostProcForOpen() {
  *op_info = "trigger=acPostProcForOpen, chksum=$chksum,"
          ++ " connectOption=$connectOption, dataId=$dataId,"
          ++ " dataSize=$dataSize, dataType=$dataType, destRescName=$destRescName,"
          ++ " filePath=$filePath, objPath=$objPath, replNum=$replNum, replStatus=$replStatus,"
          ++ " rescName=$rescName, rodsZoneClient=$rodsZoneClient, rodsZoneProxy=$rodsZoneProxy,"
          ++ " userNameClient=$userNameClient, userNameProxy=$userNameProxy, writeFlag=$writeFlag,"
          ++ " clientAddr=$clientAddr"

  if ($userNameClient != "anonymous") {  
    msiExecCmd("rabbitclient.py", "seadatacloud user_op '*op_info'",
               "null", "null", "null", *outMessage);
    msiGetStderrInExecCmdOut(*outMessage, *output);
  }
}

# it triggers irm -r collection
acPostProcForRmColl() {
  *op_info = "trigger=acPostProcForRmColl, collName=$collName,"
          ++ " collParentName=$collParentName, connectOption=$connectOption,"
          ++ " rodsZoneClient=$rodsZoneClient, rodsZoneProxy=$rodsZoneProxy,"
          ++ " userNameClient=$userNameClient, clientAddr=$clientAddr"

  writeLine( "serverLog", "DEBUG: *op_info");
  if ($userNameClient != "anonymous") {
    msiExecCmd("rabbitclient.py", "seadatacloud user_op '*op_info'",
               "null", "null", "null", *outMessage);
    msiGetStderrInExecCmdOut(*outMessage, *output);
  }
}

# it triggers irm
acPostProcForDelete() {
  *op_info = "trigger=acPostProcForDelete, chksum=$chksum,"
          ++ " connectOption=$connectOption, dataId=$dataId,"
          ++ " dataSize=$dataSize, dataType=$dataType, destRescName=$destRescName,"
          ++ " filePath=$filePath, objPath=$objPath, replNum=$replNum, replStatus=$replStatus,"
          ++ " rescName=$rescName, rodsZoneClient=$rodsZoneClient, rodsZoneProxy=$rodsZoneProxy,"
          ++ " userNameClient=$userNameClient, userNameProxy=$userNameProxy, writeFlag=$writeFlag,"
          ++ " clientAddr=$clientAddr"

  if ($userNameClient != "anonymous") {
    msiExecCmd("rabbitclient.py", "seadatacloud user_op '*op_info'",
               "null", "null", "null", *outMessage);
    msiGetStderrInExecCmdOut(*outMessage, *output);
  }
}
