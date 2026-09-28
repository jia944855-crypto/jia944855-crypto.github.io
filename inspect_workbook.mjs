import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const inputPath = '/Users/yanglijia/Desktop/history对照表.xlsx';
const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const summary = await workbook.inspect({ kind: 'workbook,sheet,table', maxChars: 12000, tableMaxRows: 30, tableMaxCols: 20, tableMaxCellChars: 120 });
console.log(summary.ndjson);
const sheets = workbook.worksheets;
for (let i = 0; i < sheets.items.length; i++) {
  const sheet = sheets.items[i];
  const used = sheet.getUsedRange();
  console.log(`SHEET ${i}: ${sheet.name}`);
  console.log('USED', used ? used.address : 'none');
  if (used) {
    const region = await workbook.inspect({ kind: 'region', sheetId: sheet.name, range: used.address, maxChars: 20000, tableMaxRows: 100, tableMaxCols: 40, tableMaxCellChars: 200 });
    console.log(region.ndjson);
  }
}
const outDir = '/Users/yanglijia/Desktop/翻译项目/inspect_output';
await fs.mkdir(outDir, { recursive: true });
for (let i = 0; i < sheets.items.length; i++) {
  const sheet = sheets.items[i];
  const preview = await workbook.render({ sheetName: sheet.name, autoCrop: 'all', scale: 1, format: 'png' });
  await fs.writeFile(`${outDir}/sheet_${i}.png`, new Uint8Array(await preview.arrayBuffer()));
}
