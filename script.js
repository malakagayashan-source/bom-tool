function processFile() {
  const file = document.getElementById('fileInput').files[0];
  const reader = new FileReader();

  reader.onload = function(e) {
    const data = new Uint8Array(e.target.result);
    const workbook = XLSX.read(data, { type: 'array' });

    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    const jsonData = XLSX.utils.sheet_to_json(sheet);

    const result = explodeBOM(jsonData);
    displayTable(result);
  };

  reader.readAsArrayBuffer(file);
}

// 🔥 Replace this with your real logic
function explodeBOM(data) {
  let output = [];

  data.forEach(row => {
    output.push({
      Parent: row.Parent,
      Child: row.Child,
      Qty: row.Qty
    });
  });

  return output;
}

function displayTable(data) {
  const table = document.getElementById("outputTable");
  table.innerHTML = "";

  if (data.length === 0) return;

  const headers = Object.keys(data[0]);
  let headerRow = "<tr>" + headers.map(h => `<th>${h}</th>`).join("") + "</tr>";
  table.innerHTML += headerRow;

  data.forEach(row => {
    let rowHTML = "<tr>" + headers.map(h => `<td>${row[h]}</td>`).join("") + "</tr>";
    table.innerHTML += rowHTML;
  });
}
