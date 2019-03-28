from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint
import time


def deletebatchJobs(batch_api,configs):
    name = configs.interferenceType
    namespace = configs.testNS

    try: 
        api_response = batch_api.delete_namespaced_job(name, namespace, pretty='true', grace_period_seconds=2)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling BatchV1Api->delete_namespaced_job: %s\n" % e)



def clusterSetup(api_instance, batch_api, configs):
    for deployment, replicaCnt in configs.workflowDeplList.iteritems():
        # setup correct pod replica count for workflow deployments 
        try: 
            workflow_depl = api_instance.read_namespaced_deployment(
                name=deployment,
                namespace=configs.testNS,
                pretty='true',
                exact=True,
                export=True)

            workflow_depl.spec.replicas = int(replicaCnt)
            print("\nUpdating deployment %s with replicaCnt %d\n" % (deployment, workflow_depl.spec.replicas))
            updated_depl = api_instance.patch_namespaced_deployment(
                name=deployment,
                namespace=configs.testNS,
                body=workflow_depl)
            
            #check to confirm that replica cnt is now at correct amount
            ready = False
            for i in range(10):
                time.sleep(3)
                check_depl = api_instance.read_namespaced_deployment(
                    name=deployment,
                    namespace=configs.testNS,
                    pretty='true',
                    exact=True,
                    export=True)
                if check_depl.spec.replicas == int(replicaCnt):
                    print("--Deployment %s updated to replica cnt='%d'" % (updated_depl.metadata.name, updated_depl.spec.replicas))
                    ready = True
                    break

            if ready == False:    
                print("-- Deployment %s not able to be updated within 30sec! ---\n" % deployment)
        
        except ApiException as e:
            print("Exception when calling AppsV1Api->read_namespaced_deployment: %s\n" % e)


    # TODO: place interference deployment in correct zone w/ correct count
    namespace=configs.testNS 
    pretty = 'true' # str | If 'true', then the output is pretty printed. (optional)
    if configs.interferenceLvl > 0:
        body = load_yaml_job_spec(10,configs.interferenceLvl,configs.interferenceZone, configs.interferenceType)
        try: 
            api_response = batch_api.create_namespaced_job(namespace=namespace, body=body, pretty=pretty)
            pprint(api_response)
        except ApiException as e:
            print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)



def load_yaml_job_spec(cntCompletions=10,cntParallelism=2,zone="red",jobType="stream"):
    import yaml 
    body = None
    if jobType == "stream" or "":
        with open('stream.yaml','r') as f:
            body = yaml.load(f) 
            pprint(body)
    if body != None:    
        '''
        body.spec.parallelism = cntParallelism
        body.spec.completions = cntCompletions
        zoneSelector  = {}
        zoneSelector['color'] = zone
        body.spec.template.spec.node_selector = zoneSelector
        '''
        body['spec']['parallelism'] = int(cntParallelism)
        body['spec']['completions'] = int(cntCompletions)
        body['spec']['template']['spec']['nodeSelector']['color'] = zone 
        

    return body 




    
def create_batch_job_spec(cntCompletions=10,cntParallelism=2,zone="red",jobType="memory"):
    body = client.V1Job() # V1Job | 
    print(body)
    body.kind = "Job"
    body.spec.parallelism = cntParallelism
    body.spec.completions = cntCompletions
    #TODO: Remove ""
    if joyType=="" or jobType=="memory":
        body.metadata.name  = "stream"
        body.spec.template.metdata.name = "stream-pod"
        body.spec.template.spec.containers.name = "stream-container"
        body.spec.template.spec.containers.image = "joyrahman/stream3:v8"
    
    zoneSelector = dict()
    #TODO: remove zone null check
    if zone is None:
        zone == "red"
    zoneSelector['color'] = zone
    body.spec.template.spec.node_selector = zoneSelector

    return body
