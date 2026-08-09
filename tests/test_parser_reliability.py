import unittest

from parser_engine import extract_items, parse_invoice


SAP_INVOICE_TEXT = """
הפדרציה הישראלית לתקליטים וקלטות בע"מ
מספר ע.מ. 511355331
>{programname:SAP;company:FED2008_HE;doctype:13;id:3802
לכבוד
09/07/2026 תאריך: מפגש הדייגים בע"מ
מספר ע.מ. 517307666
מקור חשבונית מס 26/ 3802
סה"כ מחיר כמות תיאור קוד פריט #
1 תמלוגים לשנת 2026 לתקופה 31.12.26 - 22.6.26 2026 1
1 בגין השמעת מוסיקה מוקלטת 12 2
1,756.56 ₪ 3,378.00 ₪ 0.52 מסעדה 51 עד 100 איש 501 3
1,756.56 ₪ סה"כ לפני מע"מ
316.22 ₪ מע"מ 18.00 %
2,073.00 ₪ סה"כ לתשלום
"""


class ParserReliabilityTests(unittest.TestCase):
    def test_unknown_supplier_uses_issuer_header_not_recipient(self):
        invoice = parse_invoice(SAP_INVOICE_TEXT)

        self.assertEqual(invoice["supplier"], 'הפדרציה הישראלית לתקליטים וקלטות בע"מ')
        self.assertEqual(invoice["supplier_id"], "511355331")
        self.assertEqual(invoice["invoice_number"], "26/3802")
        self.assertEqual(invoice["invoice_date"], "2026-07-09")

    def test_vat_and_totals_are_read_from_their_own_rows(self):
        invoice = parse_invoice(SAP_INVOICE_TEXT)

        self.assertEqual(invoice["subtotal"], 1756.56)
        self.assertEqual(invoice["vat"], 316.22)
        self.assertEqual(invoice["total"], 2073.0)

    def test_sap_lines_are_available_for_review(self):
        items = extract_items(SAP_INVOICE_TEXT)

        self.assertEqual(len(items), 3)
        self.assertEqual(items[-1]["קוד מוצר"], "501")
        self.assertEqual(items[-1]["כמות"], 0.52)
        self.assertEqual(items[-1]['סה"כ שורה'], 1756.56)


if __name__ == "__main__":
    unittest.main()
