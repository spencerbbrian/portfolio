import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

class TransformData(beam.DoFn):
    def process(self, element):
        element['TotalSales'] = float(element['Quantity']) * float(element['Price'])
        yield element

def run():
    options = PipelineOptions(
        runner = 'FlinkRunner',
        region = 'us-east-2',
        temp_location = 's3://my-ecommerce-bucket123/temp',
        staging_location = 's3://my-ecommerce-bucket123/staging'
    )

    with beam.Pipeline(options=options) as p:
        (p
            | 'Read CSV' >> beam.io.ReadFromText('s3://my-ecommerce-bucket123/data/ecommerce_data.csv', skip_header_lines=1)
            | 'Parse CSV' >> beam.Map(lambda x: dict(zip(('ProductID', 'ProductName', 'Quantity', 'Price'), x.split(','))))
            | 'Transform Data' >> beam.ParDo(TransformData())
            | 'Write to S3' >> beam.io.WriteToText('s3://my-ecommerce-bucket123/output/',file_name_suffix='.json')
        )

if __name__ == '__main__':
    run()