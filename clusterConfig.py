from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint
import time

def clusterSetup(api_instance, configs):
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

    # TODO: place interference job in correct zone w/ correct count
    

    
