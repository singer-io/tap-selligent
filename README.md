# tap-selligent

Author: Connor McArthur (connor@fishtownanalytics.com)

This is a [Singer](https://singer.io) tap that produces JSON-formatted data following the [Singer spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:
- Pulls raw data from Selligent's API
- Extracts the following resources:
  - Programs
  - Transactional Mailings
  - Data sources (internal & external)
- Outputs the schema for each resource
- Writes all data on each run


## Quick start

1. Install

    ```bash
    > git clone git@github.com:fishtown-analytics/tap-selligent.git
    > cd tap-selligent
    > pip install .
    ```

2. Get credentials from Taboola:

    You'll need:

    - Your Selligent organization name (if you aren't sure, contact your account manager)
    - An API key for your organization
    - The base URL for your Selligent installation

3. Create the config file.

    There is a template you can use at `config.json.example`, just copy it to `config.json`
    in the repo root and insert your credentials.
 
    - `organization`, your Selligent organization name (looks like "Organization")
    - `api_key`, your API Key
    - `base_url`, the base URL of your Selligent installation (looks like "https://organization.yourhost.com:443")
    - `user_agent`, the user-agent to set as a header on all requests made. Include your email address. (example: "tap-selligent (you@yourdomain.com)")
    - `start_date`, the date from which you want to sync data, in the format `2017-03-10`.

4. Run the application.

   ```bash
   tap-selligent --config config.json
   ```

---

Copyright &copy; 2017 Fishtown Analytics
