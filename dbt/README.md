# Mix Energy DBT Project
This directory contains the DBT (Data Build Tool) project for Mix Energy. DBT is a powerful tool for transforming data in your warehouse by writing SQL SELECT statements. It allows you to manage your data transformations in a modular and version-controlled way.

## Configuration
### profiles.yml
The `profiles.yml` file is located in /home/yourfolder/.dbt/profiles.yml. It contains the connection configurations for your DBT project. Below is an example configuration for connecting to a BigQuery data warehouse:

You should copy the following configuration into your `profiles.yml` file, making sure to replace the placeholders with your actual project details and credentials:
```yaml
mix_energy_dbt:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: mix-energie-gcp   # BigQuery project ID
      schema: dev_mix_energie   # BigQuery dataset/schema to use for development
      keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"   # Path to the service account key file
      threads: 1
      timeout_seconds: 300
      location: europe-west1
    prod:
      type: bigquery
      method: service-account
      project: mix-energie-gcp   # BigQuery project ID
      schema: prod_mix_energie   # BigQuery dataset/schema to use for production
      keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"   # Path to the service account key file
      threads: 1
      timeout_seconds: 300
      location: europe-west1
```
## Usage
To run your DBT project, you can use the following commands in your terminal:
- `dbt compile`: Compiles your SQL models without executing them, allowing you to review the generated SQL. (--target dev by default if not specified).
- `dbt compile --target dev`: Compiles using the development configuration.
- `dbt compile --target prod`: Compiles using the production configuration.
- `dbt run`: Executes the SQL transformations defined in your models (--target dev by default if not specified).
- `dbt run --target dev`: Executes the SQL transformations defined in your models using the development configuration.
- `dbt run --target prod`: Executes the SQL transformations defined in your models using the production configuration.
- `dbt clean`: Cleans up the target directory by removing compiled files and artifacts.
- `dbt docs generate`: Generates documentation for your DBT project, which can be viewed in a web browser.
- `dbt docs serve`: Serves the generated documentation on a local web server, localhost:8080 by default.
Make sure to set the appropriate environment variables for your service account key file before running the commands, especially if you are using the BigQuery connection method. You can set the environment variable in your terminal like this:
```bashexport GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```
## Conclusion
This DBT project is set up to manage and transform data for Mix Energy using BigQuery as the data warehouse. By organizing your transformations in DBT, you can ensure that your data pipeline is maintainable, version-controlled, and scalable as your data needs grow.  Make sure to customize the configurations in `profiles.yml` and `dbt_project.yml` according to your specific project requirements and data warehouse setup.  Happy data modeling!
