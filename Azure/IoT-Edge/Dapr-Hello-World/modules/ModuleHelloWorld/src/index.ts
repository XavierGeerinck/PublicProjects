import Dapr, { Req, Res } from "@roadwork/dapr-js-sdk";

async function main() {
  const client = new Dapr("127.0.0.1", 3500);

  await client.invoker.listen("main", async (req: Req, res: Res) => {
    console.log(req.body);
    return res.json({ message: "Hello World" });
  });
}

main()
.catch((e) => {
  console.error(e);
  process.exit(1);
});