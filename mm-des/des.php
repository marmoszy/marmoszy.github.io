<?php
//echo "<pre>".$_REQUEST["ex"]."</pre>";
function base64url_encode($data) {
  return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
}
function encode($data) {
  return base64url_encode(gzcompress($data));
}
if(array_key_exists("ex",$_REQUEST)) {
	file_put_contents("des.in",$_REQUEST["ex"]);
	echo "<pre>".shell_exec('C:\Users\marmo\AppData\Local\Programs\Python\Python39\python.exe des.py des.in')."</pre>";
	echo "<div>".file_get_contents("des_bpmn.svg")."</div>";
	//echo "<pre>".file_get_contents("des.out")."</prev>";
	echo "<div>".file_get_contents("des.svg")."</div>";
} else if(array_key_exists("dot",$_REQUEST)) {
	$dot=file_get_contents($_REQUEST["dot"]);
	$enco=encode($dot);
	//echo '<a href="https://kroki.io/graphviz/svg/'.$enco.'">des.dot</a>';
	echo '<meta http-equiv="Refresh" content="0; url=https://kroki.io/graphviz/svg/'.$enco.'"/>';
} else if(array_key_exists("bpmn",$_REQUEST)) {
	$bpmn=file_get_contents($_REQUEST["bpmn"]);
	$enco=encode($bpmn);
	echo '<meta http-equiv="Refresh" content="0; url=https://kroki.io/bpmn/svg/'.$enco.'"/>';
}
?>