let [method, url, headers, body, data, json, encoding, callback] = arguments;

if (data) {
  const formData = new FormData();
  for (const key in data) {
    formData.append(key, data[key]);
  }
  body = formData;
} else if (json) {
  body = JSON.stringify(json);
}

const response = await fetch(url, { method, headers, body });
response.arrayBuffer()
  .then(buffer => {
    const decoder = new TextDecoder(encoding);
    return [response.headers, decoder.decode(buffer)];
  })
  .then(([headers, text]) => callback({ headers, text }))
  ;
