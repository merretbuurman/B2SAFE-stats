# The following rule sends accounting info of type "access" / "user_login"
# Received from Claudio Cacciari

# This code is to be copied into:
# /etc/irods/core.re

pep_auth_agent_auth_response_pre(*INSTANCE_NAME, *CONTEXT, *OUT, *RESPONSE) {

  writeLine("serverLog","DEBUG:pep_auth_agent_auth_response_pre");
 
  *pairs = split(str(*CONTEXT), "++++");
  *user_info = "";
  foreach(*pair in *pairs) {
    *key = elem(split(*pair, "="), 0);
    if (*key == "auth_scheme") { *user_info = *user_info ++ *pair ++ ", "; }
    else if (*key == "client_addr") { *user_info = *user_info ++ *pair ++ ", "; }
    else if (*key == "proxy_rods_zone") { *user_info = *user_info ++ *pair ++ ", "; }
    else if (*key == "proxy_user_name") { *user_info = *user_info ++ *pair ++ ", "; }
    else if (*key == "user_rods_zone") { *user_info = *user_info ++ *pair ++ ", "; }
    else if (*key == "user_user_name") { *user_info = *user_info ++ *pair; }
  }
  writeLine("serverLog", "INFO: USER CONNECTION INFORMATION *user_info");

  if (*CONTEXT.user_user_name != "anonymous") {
    msiExecCmd("rabbitclient.py", "seadatacloud user_login '*user_info'",
               "null", "null", "null", *outMessage);
    msiGetStderrInExecCmdOut(*outMessage, *output);
  }
}
