from datetime import datetime

from flask import Blueprint, jsonify, render_template,request
import cx_Oracle
from contextlib import closing
import oracledb
from decimal import Decimal
import logging

from function.pdf_creation import generate_pdf

oracledb.init_oracle_client(lib_dir=r"D:\instantclient_23_6")

nesba_blueprint = Blueprint('nesba', __name__, template_folder='templates')

# Building mapping dictionary
building_map = {
    1: "مستشفي الجراحة",
    2: "مستشفى الباطنة",
    3: "مستشفى الجهاز التنفسي",
    4: "مستشفى الاسنان التخصصي",
    5: "مستشفى الطوارئ والحوادث",
    6: "مستشفى الكلى",
    7: "مستشفى القلب ",
    8: "مستشفى العيون التخصصي",
    9: " مركز السموم"
}
global query


# Function to calculate totals
# ased on conditions
def total_fun(arr, start, end, total_over, even):
    sum_val = 0
    for i, el in enumerate(arr):
        if start <= i <= end:
            if even and i % 2 == 0:
                sum_val += el
            elif not even and i % 2 != 0:
                sum_val += el
    return f"%{round((sum_val / total_over) * 100)}"


# Database connection configuration
DB_CONFIG = {
    "user": "HOSPUSER",
    "password": "hosp",
    "dsn": "128.16.7.5:1521/hosp1121",  # Format: hostname:port/sid
}


# -------- Helpers --------
def to_int(val):
    """حوّل أى قيمة عددية إلى int، وإلا ارجع None"""
    if val in (None, ''):
        return None
    if isinstance(val, (int,)):
        return val
    if isinstance(val, float):
        return int(round(val))
    if isinstance(val, Decimal):
        return int(val)
    try:
        return int(float(str(val).replace(',', '')))
    except ValueError:
        return None


def nz(v):
    n = to_int(v)
    return n if n is not None else 0


def get_data():
    query = """
SELECT BUILDING, 
      (BED_STORE1_CNT + BED_STORE2_CNT + BED_WRK1_CNT + BED_WRK2_CNT) as total_sum,
      BED_STORE1_CNT, BED_STORE2_CNT, BED_WRK1_CNT,
      BED_WRK2_CNT, worker1, worker2, DOBAT_1, DOBAT_2, SAF1, SAF2,
      DOBAT_F1, DOBAT_F2, SAF_F1, SAF_F2,
      MADNY1, MADNY2, MORAFK1, MORAFK2, BEDS_CNT,

      CASE 
      WHEN NVL(BED_WRK1_CNT, 0) = 0 THEN '%0'
      ELSE '%' || TO_CHAR(ROUND(((NVL(DOBAT_1, 0) + NVL(SAF1, 0) + NVL(DOBAT_F1, 0) + NVL(SAF_F1, 0) + NVL(MADNY1, 0) + NVL(MORAFK1, 0)) / NVL(BED_WRK1_CNT, 1) * 100))
      END AS BED_RAT1,

      CASE 
      WHEN NVL(BED_WRK2_CNT, 0) = 0 THEN '%0'
      ELSE '%' || TO_CHAR(ROUND(((NVL(DOBAT_2, 0) + NVL(SAF2, 0) + NVL(DOBAT_F2, 0) + NVL(SAF_F2, 0) + NVL(MADNY2, 0) + NVL(MORAFK2, 0)) / NVL(BED_WRK2_CNT, 1) * 100))
      END AS BED_RAT2,

      CASE 
      WHEN NVL(BED_WRK1_CNT, 0) + NVL(BED_WRK2_CNT, 0) = 0 THEN '%0'
      ELSE '%' || TO_CHAR(ROUND(((NVL(BEDS_CNT, 0)) / (NVL(BED_WRK1_CNT, 0) + NVL(BED_WRK2_CNT, 0)) * 100))
      END AS BED_RAT_TOTAL  

FROM (
    SELECT
          BUILDING.BUILDING_NUM as BUILDING,
          NVL(
            (SELECT SUM(NVL(ROOM.BED_COUNT, 0))
            FROM ROOM, WARD
            WHERE ROOM.F_W_CODE = WARD.F_W_CODE
              AND ROOM_CASE = 1
              AND ROOM_TYPE = 1
              AND WARD.BUILDING_NUM = BUILDING.BUILDING_NUM),
            0
          ) AS BED_STORE1_CNT,
          NVL(
            (SELECT SUM(NVL(ROOM.BED_COUNT, 0))
            FROM ROOM, WARD
            WHERE ROOM.F_W_CODE = WARD.F_W_CODE
              AND ROOM_CASE = 1
              AND ROOM_TYPE = 2
              AND WARD.BUILDING_NUM = BUILDING.BUILDING_NUM),
            0
          ) AS BED_STORE2_CNT,
          NVL(
            (SELECT SUM(NVL(ROOM.BED_COUNT, 0))
            FROM ROOM, WARD
            WHERE ROOM.F_W_CODE = WARD.F_W_CODE
              AND ROOM_CASE = 0
              AND ROOM_TYPE = 1
              AND WARD.BUILDING_NUM = BUILDING.BUILDING_NUM),
            0
          ) AS BED_WRK1_CNT,
        NVL(
            (SELECT SUM(NVL(ROOM.BED_COUNT, 0))
            FROM ROOM, WARD
            WHERE ROOM.F_W_CODE = WARD.F_W_CODE
              AND ROOM_CASE = 0
              AND ROOM_TYPE = 2
              AND WARD.BUILDING_NUM = BUILDING.BUILDING_NUM),
            0
          ) AS BED_WRK2_CNT,

          SUM(CASE WHEN PATIENT.RANK IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 22) AND ROOM.ROOM_TYPE = 1 THEN 1 ELSE 0 END) DOBAT_1, 
          SUM(CASE WHEN PATIENT.RANK IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 22) AND ROOM.ROOM_TYPE = 2 THEN 1 ELSE 0 END) DOBAT_2, 
          SUM(CASE WHEN PATIENT.RANK IN (12, 13, 14, 15, 16, 17, 18, 19, 23) AND ROOM.ROOM_TYPE = 1 THEN 1 ELSE 0 END) SAF1,
          SUM(CASE WHEN PATIENT.RANK IN (12, 13, 14, 15, 16, 17, 18, 19, 23) AND ROOM.ROOM_TYPE = 2 THEN 1 ELSE 0 END) SAF2,
          SUM(CASE WHEN PATIENT.RANK = 20 AND ROOM.ROOM_TYPE = 1 AND PATIENT.KINSHIP_PATIENT_NUM IS NOT NULL AND P2.RANK IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 22) THEN 1 ELSE 0 END) DOBAT_F1,
          SUM(CASE WHEN PATIENT.RANK = 20 AND ROOM.ROOM_TYPE = 2 AND PATIENT.KINSHIP_PATIENT_NUM IS NOT NULL AND P2.RANK IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 22) THEN 1 ELSE 0 END) DOBAT_F2,
          SUM(CASE WHEN PATIENT.RANK = 20 AND ROOM.ROOM_TYPE = 1 AND PATIENT.KINSHIP_PATIENT_NUM IS NOT NULL AND P2.RANK IN (12, 13, 14, 15, 16, 17, 18, 19, 23) THEN 1 ELSE 0 END) SAF_F1,
          SUM(CASE WHEN PATIENT.RANK = 20 AND ROOM.ROOM_TYPE = 2 AND PATIENT.KINSHIP_PATIENT_NUM IS NOT NULL AND P2.RANK IN (12, 13, 14, 15, 16, 17, 18, 19, 23) THEN 1 ELSE 0 END) SAF_F2,
          SUM(CASE WHEN PATIENT.RANK = 20 AND ROOM.ROOM_TYPE = 1 AND PATIENT.KINSHIP_PATIENT_NUM IS NULL THEN 1 ELSE 0 END) MADNY1,
          SUM(CASE WHEN PATIENT.RANK = 20 AND ROOM.ROOM_TYPE = 2 AND PATIENT.KINSHIP_PATIENT_NUM IS NULL THEN 1 ELSE 0 END) MADNY2,
          SUM(CASE WHEN EXISTS (SELECT 1 FROM ASSOCIATION_IN_ROOM WHERE PATIENT_GOING_IN_ROOM.PATIENT_NUM = ASSOCIATION_IN_ROOM.PATIENT_NUM) AND ROOM.ROOM_TYPE = 1 THEN 1 ELSE 0 END) MORAFK1,
          SUM(CASE WHEN EXISTS (SELECT 1 FROM ASSOCIATION_IN_ROOM WHERE PATIENT_GOING_IN_ROOM.PATIENT_NUM = ASSOCIATION_IN_ROOM.PATIENT_NUM) AND ROOM.ROOM_TYPE = 2 THEN 1 ELSE 0 END) MORAFK2,
          SUM(CASE WHEN PATIENT.RANK IN (29) AND ROOM.ROOM_TYPE = 1 THEN 1 ELSE 0 END) worker1,
          SUM(CASE WHEN PATIENT.RANK IN (29) AND ROOM.ROOM_TYPE = 2 THEN 1 ELSE 0 END) worker2,
          COUNT(*) BEDS_CNT
    FROM   PATIENT, PATIENT_IN, PATIENT_GOING_IN_ROOM, ROOM, WARD, BUILDING, ARRIVAL, PATIENT P2
    WHERE PATIENT.PATIENT_NUM = PATIENT_IN.PATIENT_NUM
    AND     PATIENT.PATIENT_NUM = PATIENT_GOING_IN_ROOM.PATIENT_NUM
    AND     PATIENT.PATIENT_NUM = ARRIVAL.PATIENT_NUM
    AND     PATIENT_IN.PRESENT_IN = 1
    AND     PATIENT.PATIENT_NUM <> 0
    AND     PATIENT.KINSHIP_PATIENT_NUM = P2.PATIENT_NUM(+)
    AND     PATIENT_GOING_IN_ROOM.GOING_OUT_DATE IS NULL
    AND     PATIENT_GOING_IN_ROOM.GOING_OUT_TIME IS NULL
    AND     PATIENT_GOING_IN_ROOM.ROOM_NUM = ROOM.ROOM_NUM
    AND     ROOM.F_W_CODE = WARD.F_W_CODE
    AND     PATIENT_GOING_IN_ROOM.ARIVAL_SERIAL = PATIENT_IN.ARIVAL_SERIAL
    AND     PATIENT_IN.ARIVAL_SERIAL = ARRIVAL.ARIVAL_SERIAL
    AND     WARD.BUILDING_NUM = BUILDING.BUILDING_NUM
    GROUP BY BUILDING.BUILDING_NUM
    UNION
    SELECT BUILDING.BUILDING_NUM, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    FROM   BUILDING
    WHERE NOT EXISTS (SELECT 1
                      FROM    PATIENT, PATIENT_IN, PATIENT_GOING_IN_ROOM, PATIENT P2, ROOM, WARD
                      WHERE  PATIENT.PATIENT_NUM = PATIENT_IN.PATIENT_NUM
                      AND      PATIENT.PATIENT_NUM = PATIENT_GOING_IN_ROOM.PATIENT_NUM
                      AND      PATIENT_IN.PRESENT_IN = 1
                      AND      PATIENT.PATIENT_NUM <> 0
                      AND      PATIENT.KINSHIP_PATIENT_NUM = P2.PATIENT_NUM(+)
                      AND      ROOM.F_W_CODE = WARD.F_W_CODE
                      AND     WARD.BUILDING_NUM = BUILDING.BUILDING_NUM
                      AND      PATIENT_GOING_IN_ROOM.GOING_OUT_DATE IS NULL
                      AND      PATIENT_GOING_IN_ROOM.GOING_OUT_TIME IS NULL
                      AND      PATIENT_GOING_IN_ROOM.ROOM_NUM = ROOM.ROOM_NUM)
    ORDER BY 1
)
ORDER BY BUILDING
"""
    try:
        # 1) Fetch data from Oracle
        with closing(cx_Oracle.connect(**DB_CONFIG)) as con, closing(con.cursor()) as cur:
            cur.execute(query)
            db_cols = [c[0] for c in cur.description]  # Column names
            raw_rows = [dict(zip(db_cols, r)) for r in cur.fetchall()]

        # 2) Replace building number with name
        for r in raw_rows:
            r['BUILDING_NAME'] = building_map.get(r.pop('BUILDING'), 'Unknown')

        # 3) Order hospitals
        custom_order = [
            "مستشفي الجراحة", "مستشفى الباطنة",
            "مستشفى الجهاز التنفسي", "مستشفى الاسنان التخصصي",
            "مستشفى الطوارئ والحوادث", "مستشفى الكلى",
            "مستشفى القلب ", "مستشفى العيون التخصصي",
            " مركز السموم"
        ]
        idx = {n: i for i, n in enumerate(custom_order)}
        raw_rows.sort(key=lambda r: idx.get(r['BUILDING_NAME'], 999))

        # 4) Calculate occupied beds + convert all numbers to int
        for r in raw_rows:
            r['BEDS_OCC_EGAMA'] = sum([
                nz(r['DOBAT_1']), nz(r['SAF1']), nz(r['DOBAT_F1']),
                nz(r['SAF_F1']), nz(r['MADNY1']), nz(r['MORAFK1']),
                nz(r['WORKER1'])
            ])
            r['BEDS_OCC_RAYAA'] = sum([
                nz(r['DOBAT_2']), nz(r['SAF2']), nz(r['DOBAT_F2']),
                nz(r['SAF_F2']), nz(r['MADNY2']), nz(r['MORAFK2']),
                nz(r['WORKER2'])
            ])
            r['BEDS_CNT'] = r['BEDS_OCC_EGAMA'] + r['BEDS_OCC_RAYAA']

            # Ensure all numeric values are int
            for k, v in r.items():
                iv = to_int(v)
                if iv is not None:
                    r[k] = iv

        # 5) Order columns according to header
        ordered_cols = [
            'BUILDING_NAME', 'TOTAL_SUM',
            'BED_STORE1_CNT', 'BED_STORE2_CNT',
            'BED_WRK1_CNT', 'BED_WRK2_CNT',
            'DOBAT_1', 'DOBAT_2',
            'SAF1', 'SAF2',
            'WORKER1', 'WORKER2',
            'DOBAT_F1', 'DOBAT_F2',
            'SAF_F1', 'SAF_F2',
            'MADNY1', 'MADNY2',
            'MORAFK1', 'MORAFK2',
            # Occupied beds
            'BEDS_OCC_EGAMA', 'BEDS_OCC_RAYAA', 'BEDS_CNT',
            # Occupancy rates
            'BED_RAT1', 'BED_RAT2', 'BED_RAT_TOTAL'
        ]
        extra_cols = [c for c in db_cols if c not in ordered_cols and c != 'BUILDING']
        columns = ordered_cols + extra_cols

        # 6) Reorder rows
        rows = [{col: raw.get(col, '') for col in columns} for raw in raw_rows]

        # 7) "Total" row
        total_row = {'BUILDING_NAME': 'الإجمالى'}

        # Totals for working and occupied beds
        tot_wrk1 = sum(nz(r['BED_WRK1_CNT']) for r in rows)
        tot_wrk2 = sum(nz(r['BED_WRK2_CNT']) for r in rows)
        tot_occ1 = sum(nz(r['BEDS_OCC_EGAMA']) for r in rows)
        tot_occ2 = sum(nz(r['BEDS_OCC_RAYAA']) for r in rows)

        def pct(num, den):
            return f"{round((num / den) * 100)}%" if den else '0%'

        bed_rat1_total = pct(tot_occ1, tot_wrk1)
        bed_rat2_total = pct(tot_occ2, tot_wrk2)
        bed_rat_total_all = pct(tot_occ1 + tot_occ2, tot_wrk1 + tot_wrk2)

        for col in columns[1:]:
            if col == 'BED_RAT1':
                total_row[col] = bed_rat1_total
            elif col == 'BED_RAT2':
                total_row[col] = bed_rat2_total
            elif col == 'BED_RAT_TOTAL':
                total_row[col] = bed_rat_total_all
            else:
                nums = [to_int(r[col]) for r in rows if to_int(r[col]) is not None]
                total_row[col] = sum(nums) if nums else ''

        rows.append(total_row)

        # 8) Check output format
        output_format = request.args.get('format', 'html').lower()

        if output_format == 'pdf':
            # Prepare data for PDF
            pdf_data = {
                'columns': columns,
                'rows': rows,
                'title': 'تقرير نسب الأشغال',
                'now': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Generate landscape PDF for wide tables
            return generate_pdf('table_pdf.html', pdf_data,
                                title='نسب الأشغال',
                                orientation='landscape')
        else:
            # Default HTML output
            return render_template('table.html', columns=columns, rows=rows)

    except Exception as e:
        logging.exception("Error fetching data")
        return jsonify({"error": str(e)}), 500