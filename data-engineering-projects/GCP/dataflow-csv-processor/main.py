import apache_beam as beam
import argparse


def get_student_info(line):
  if line:
    try:
      student_id = line[1]
      age = int(line[8])
      # Determine age group
      if age <= 18:
        age_group = 'underage'
      elif age <= 59:
        age_group = 'adult'
      else:
        age_group = 'elderly'
      return student_id, age_group
    except (KeyError, ValueError):
      pass
  return None


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Get student info')
  parser.add_argument('--output', default='gs://dataflow_csv_processor/output/student_data_grouped')
  parser.add_argument('--input', default='gs://dataflow_csv_processor/golheights_students.csv')

  options, pipeline_args = parser.parse_known_args()
  p = beam.Pipeline(argv=pipeline_args)

  (p
   | 'ReadFromCSV' >> beam.io.ReadFromText(options.input, skip_header_lines=1)
   | 'SplitLines' >> beam.Map(lambda line: line.split(','))
   | 'GetInfo' >> beam.FlatMap(get_student_info)
   | 'FilterInvalid' >> beam.Filter(lambda info: info is not None)
   | 'WriteToCSV' >> beam.io.WriteToText(options.output)
  )

  p.run().wait_until_finish()
