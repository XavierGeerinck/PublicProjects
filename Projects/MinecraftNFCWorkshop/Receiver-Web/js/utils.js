function str2ab(str) {
	str = decodeURI(encodeURIComponent(str));
	var buf = new ArrayBuffer(str.length); // 2 bytes for each char
	var bufView = new Uint8Array(buf);
	for (var i = 0, strLen = str.length; i < strLen; i++) {
			bufView[i] = str.charCodeAt(i);
	}
	return buf;
}

function Utf8ArrayToStr(utfArr) {
	var out, i, len, c;
	var char2, char3;

	out = "";
	len = utfArr.length;
	i = 0;
	while (i < len) {
			c = utfArr[i++];
			switch (c >> 4) {
					case 0: case 1: case 2: case 3: case 4: case 5: case 6: case 7:
							// 0xxxxxxx
							out += String.fromCharCode(c);
							break;
					case 12: case 13:
							// 110x xxxx   10xx xxxx
							char2 = utfArr[i++];
							out += String.fromCharCode(((c & 0x1F) << 6) | (char2 & 0x3F));
							break;
					case 14:
							// 1110 xxxx  10xx xxxx  10xx xxxx
							char2 = utfArr[i++];
							char3 = utfArr[i++];
							out += String.fromCharCode(((c & 0x0F) << 12) |
									((char2 & 0x3F) << 6) |
									((char3 & 0x3F) << 0));
							break;
			}
	}

	return out;
}