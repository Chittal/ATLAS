/// <reference path="../pb_data/types.d.ts" />
/**
 * Updates the users collection with additional fields
 */
migrate((app) => {
  console.log("Updating Users collections...");

  const jsonFile = $os.readFile("./pb_migrations/schema/users-schema.json");
  const jsonStr = jsonFile.map((c) => String.fromCharCode(c)).join("");

  app.importCollectionsByMarshaledJSON(jsonStr)

  console.log("Updated Users collection successfully!")
}, (app) => { // optional revert operation
  try {
      console.log("Removing additional columns from Users collections...");

      // TODO: add logic

      console.log("Removed extra columns from Users collection successfully!");
  } catch (e) {
      // silent errors (probably already deleted)
      console.log("Failed removing extra columns from Users collection!", e);
  }
})