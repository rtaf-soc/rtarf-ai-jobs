#!/bin/bash

docker run -v $(pwd)/scripts:/configs \
--rm asia-southeast1-docker.pkg.dev/its-artifact-commons/rtarf/ads-ai-jobs:develop-54a34db \
sigmac -t es-qs -c /configs/sigma-rule-configs/seek-smb.yaml \
/configs/sigma-rules/zeek_smb_converted_win_transferring_files_with_credential_data.yml
