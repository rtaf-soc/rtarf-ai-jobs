#!/bin/bash

docker run -v $(pwd):/configs \
--rm asia-southeast1-docker.pkg.dev/its-artifact-commons/rtarf/ads-ai-jobs:develop-54a34db \
sigmac -t es-qs -c /configs/seek-smb.yaml \
/configs/zeek_smb_converted_win_susp_psexec.yml
