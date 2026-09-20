let [method, url, headers, body, data, json, encoding, callback] = arguments;

let requestBody = body;
if (data) {
  const formData = new FormData();
  for (const key in data) {
    formData.append(key, data[key]);
  }
  requestBody = formData;
} else if (json) {
  requestBody = JSON.stringify(json);
}

fetch(url, { method, headers, body: requestBody })
  .then(response => {
    const headerEntries = Object.fromEntries(response.headers.entries());
    return response.arrayBuffer().then(buffer => {
      const decoder = new TextDecoder(encoding);
      return { headers: headerEntries, text: decoder.decode(buffer) };
    });
  })
  .then(result => callback(result))
  .catch(err => {
    callback({ error: err.toString(), headers: {}, text: "" });
  });
