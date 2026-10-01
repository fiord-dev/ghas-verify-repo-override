// CodeQL (Code Scanning) に検出させるための、意図的に脆弱なサンプル。検証専用。
const { exec } = require("child_process");
const http = require("http");
const url = require("url");

http
  .createServer((req, res) => {
    const q = url.parse(req.url, true).query;
    // Command injection (js/command-line-injection)
    exec("ls " + q.dir, (err, stdout) => {
      // Reflected XSS (js/reflected-xss)
      res.end("<pre>" + q.dir + "\n" + stdout + "</pre>");
    });
  })
  .listen(8080);
