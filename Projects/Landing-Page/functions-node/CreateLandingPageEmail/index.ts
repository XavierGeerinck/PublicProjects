import { AzureFunction, Context, HttpRequest } from "@azure/functions";
import { v4 as uuidv4 } from "uuid";

const httpTrigger: AzureFunction = async function (
    context: Context,
    req: HttpRequest
): Promise<void> {
    const email = req.query.email || (req.body && req.body.email);

    context.bindings.bindingTableLandingPageEmails = {
        PartitionKey: "Email",
        RowKey: uuidv4(),
        Email: email,
    };

    context.log(`Added email ${email} to the table`);

    context.res = {
        // status: 200, /* Defaults to 200 */
        body: "Done",
    };
};

export default httpTrigger;