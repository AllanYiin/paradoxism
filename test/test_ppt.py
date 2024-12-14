from paradoxism.tools.ppt_tools import generate_ppt_outlines,generate_ppt




ppt_json,file_path=generate_ppt_outlines({"topic":'台灣碳交易的進展與現況',"pages":25})
generate_ppt(ppt_json)